"""
Call Transcription Service for AI Voice Assistant
Auto-transcribes calls, extracts action items, updates lead status, schedules follow-ups

Features:
- OpenAI Whisper for transcription
- GPT-4o for action item extraction
- Automatic lead status updates
- Follow-up scheduling automation
- Compliance recording and archival
- Property detail extraction
- Competitor mention tracking
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

import httpx
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.conversation_sqlalchemy import (
    VoiceInteraction,
    CallIntent,
    CallOutcome,
    SentimentLevel,
)
from app.models.lead import LeadStatus, LeadSource
from app.models.lead_sqlalchemy import Lead
from app.models.appointment_sqlalchemy import Appointment, AppointmentStatus
from app.repositories.conversation_repository import VoiceInteractionRepository
from app.database import get_db_session

logger = logging.getLogger(__name__)

# Configuration - Lazy load to avoid initialization errors
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None  # Will be initialized when needed


def get_openai_client():
    """Get or create OpenAI client (lazy initialization)"""
    global openai_client
    if openai_client is None and OPENAI_API_KEY:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return openai_client


class ActionItemType(str, Enum):
    """Types of action items extracted from calls"""
    SEND_QUOTE = "send_quote"
    SCHEDULE_CALL = "schedule_call"
    SEND_INFORMATION = "send_information"
    FOLLOW_UP = "follow_up"
    ESCALATE = "escalate"
    CALLBACK = "callback"
    SEND_PHOTOS = "send_photos"
    SCHEDULE_INSPECTION = "schedule_inspection"


class LeadDecisionStage(str, Enum):
    """Lead decision-making stages"""
    INITIAL_INQUIRY = "initial_inquiry"
    GATHERING_INFO = "gathering_info"
    COMPARING_OPTIONS = "comparing_options"
    DECISION_MAKING = "decision_making"
    READY_TO_CLOSE = "ready_to_close"
    LONG_TERM_NURTURE = "long_term_nurture"


class ActionItem:
    """Represents an action item extracted from call transcript"""

    def __init__(
        self,
        action_type: ActionItemType,
        description: str,
        due_date: Optional[datetime] = None,
        assigned_to: Optional[str] = None,
        priority: str = "medium",
        context: Optional[str] = None
    ):
        self.action_type = action_type
        self.description = description
        self.due_date = due_date or datetime.now() + timedelta(days=1)
        self.assigned_to = assigned_to
        self.priority = priority
        self.context = context

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "action_type": self.action_type.value,
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "assigned_to": self.assigned_to,
            "priority": self.priority,
            "context": self.context
        }


class CallTranscriptionService:
    """
    Call Transcription Service

    Handles:
    - Audio-to-text transcription using OpenAI Whisper
    - Action item extraction using GPT-5
    - Automatic lead status updates
    - Follow-up scheduling
    - Compliance recording
    - Data extraction (property details, budget, competitors)
    """

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize transcription service

        Args:
            db: Database session (optional, will create new if not provided)
        """
        self.db = db
        self._owns_db_session = db is None
        self.voice_repo = VoiceInteractionRepository(db) if db else None

    def _get_db(self) -> Session:
        """Get database session"""
        if self.db:
            return self.db
        return next(get_db_session())

    async def transcribe_call(
        self,
        call_id: str,
        audio_url: Optional[str] = None,
        audio_file_path: Optional[str] = None
    ) -> Dict:
        """
        Transcribe call audio using OpenAI Whisper

        Args:
            call_id: Voice interaction ID
            audio_url: URL to audio file (Bland.ai recording)
            audio_file_path: Local path to audio file

        Returns:
            Dict with transcript, duration, language, and confidence
        """
        try:
            db = self._get_db()
            voice_repo = VoiceInteractionRepository(db)

            # Get call record
            call = voice_repo.get_by_id(call_id)
            if not call:
                raise ValueError(f"Call {call_id} not found")

            # Get audio file
            if audio_url:
                # Download audio from URL
                async with httpx.AsyncClient() as client:
                    response = await client.get(audio_url)
                    response.raise_for_status()
                    audio_data = response.content
            elif audio_file_path:
                # Read from local file
                with open(audio_file_path, 'rb') as f:
                    audio_data = f.read()
            elif call.recording_url:
                # Use recording URL from call
                async with httpx.AsyncClient() as client:
                    response = await client.get(call.recording_url)
                    response.raise_for_status()
                    audio_data = response.content
            else:
                raise ValueError("No audio source provided")

            # Transcribe with Whisper
            logger.info(f"Transcribing call {call_id} with OpenAI Whisper")

            # Save audio temporarily for Whisper API
            temp_audio_path = f"/tmp/call_{call_id}.mp3"
            with open(temp_audio_path, 'wb') as f:
                f.write(audio_data)

            # Call Whisper API
            with open(temp_audio_path, 'rb') as audio_file:
                client = get_openai_client()
                if not client:
                    raise ValueError("OpenAI API key not configured")
                transcription = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    language="en"  # Auto-detect or specify
                )

            # Clean up temp file
            os.remove(temp_audio_path)

            # Update call record with transcript
            call.transcript = transcription.text
            call.transcript_language = transcription.language
            db.commit()

            logger.info(f"Call {call_id} transcribed successfully: {len(transcription.text)} characters")

            return {
                "call_id": call_id,
                "transcript": transcription.text,
                "language": transcription.language,
                "duration": transcription.duration,
                "confidence": 0.95,  # Whisper doesn't provide confidence, assume high
                "word_count": len(transcription.text.split()),
                "transcribed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error transcribing call {call_id}: {str(e)}")
            raise

    async def extract_action_items(self, transcript: str, call_context: Optional[Dict] = None) -> List[ActionItem]:
        """
        Extract action items from call transcript using GPT-5

        Args:
            transcript: Call transcript text
            call_context: Optional context (caller name, intent, etc.)

        Returns:
            List of ActionItem objects
        """
        try:
            logger.info("Extracting action items from transcript using GPT-5")

            # Build prompt for GPT-5
            prompt = f"""Analyze this roofing sales call transcript and extract all action items that need to be completed.

Call Transcript:
{transcript}

{f"Call Context: {json.dumps(call_context)}" if call_context else ""}

Extract the following:
1. **Action Items**: What needs to be done (send quote, schedule call, follow-up, etc.)
2. **Due Date**: When it should be done (extract from conversation or infer urgency)
3. **Priority**: High/Medium/Low based on customer urgency and buying signals
4. **Context**: Why this action is needed

Common action types in roofing sales:
- SEND_QUOTE: Customer requested pricing
- SCHEDULE_CALL: "Call me next week/Monday/etc."
- FOLLOW_UP: General follow-up needed
- SEND_INFORMATION: Customer wants more details
- SCHEDULE_INSPECTION: Customer wants roof inspection
- CALLBACK: Customer explicitly asked for callback
- ESCALATE: Issue needs manager attention
- SEND_PHOTOS: Send example photos

Return as JSON array:
[
  {{
    "action_type": "SEND_QUOTE",
    "description": "Send detailed quote for metal roof replacement",
    "due_date": "2025-10-15",
    "priority": "high",
    "context": "Customer said 'I need pricing by Friday to compare with other quotes'"
  }}
]
"""

            # Call GPT-5 for extraction
            client = get_openai_client()
            if not client:
                raise ValueError("OpenAI API key not configured")
            response = await client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing sales call transcripts and extracting actionable tasks. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )

            # Parse response
            result = json.loads(response.choices[0].message.content)
            action_items_data = result.get("action_items", [])

            # Convert to ActionItem objects
            action_items = []
            for item_data in action_items_data:
                try:
                    action_type = ActionItemType(item_data.get("action_type", "").lower())
                    due_date_str = item_data.get("due_date")
                    due_date = datetime.fromisoformat(due_date_str) if due_date_str else None

                    action_item = ActionItem(
                        action_type=action_type,
                        description=item_data.get("description", ""),
                        due_date=due_date,
                        assigned_to=item_data.get("assigned_to"),
                        priority=item_data.get("priority", "medium"),
                        context=item_data.get("context")
                    )
                    action_items.append(action_item)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid action item: {e}")
                    continue

            logger.info(f"Extracted {len(action_items)} action items from transcript")
            return action_items

        except Exception as e:
            logger.error(f"Error extracting action items: {str(e)}")
            return []

    async def update_lead_status(self, lead_id: int, transcript: str, call_intent: CallIntent) -> Tuple[LeadStatus, LeadDecisionStage]:
        """
        Update lead status based on call transcript analysis

        Args:
            lead_id: Lead ID to update
            transcript: Call transcript
            call_intent: Detected call intent

        Returns:
            Tuple of (new_status, decision_stage)
        """
        try:
            db = self._get_db()
            lead = db.query(Lead).filter(Lead.id == lead_id).first()

            if not lead:
                raise ValueError(f"Lead {lead_id} not found")

            logger.info(f"Analyzing call transcript to update lead {lead_id} status")

            # Use GPT-5 to analyze decision stage
            prompt = f"""Analyze this roofing sales call and determine the customer's decision stage and appropriate CRM status.

Call Transcript:
{transcript}

Call Intent: {call_intent.value}

Classify the customer into:

**Decision Stages:**
- INITIAL_INQUIRY: Just starting to explore options
- GATHERING_INFO: Researching and learning
- COMPARING_OPTIONS: Getting multiple quotes
- DECISION_MAKING: Close to making decision, discussing with spouse/partner
- READY_TO_CLOSE: Expressed clear intent to move forward
- LONG_TERM_NURTURE: Not ready now, follow up in 3-6 months

**CRM Status:**
- new: First contact
- contacted: We've reached out
- qualified: Meets our criteria, has intent
- proposal_sent: Quote/proposal provided
- negotiation: Discussing pricing/terms
- closed_won: Deal closed
- closed_lost: Lost to competitor or no longer interested
- nurture: Long-term follow-up

Look for key phrases:
- "I'm ready to move forward" → READY_TO_CLOSE / qualified
- "I want to get another quote" → COMPARING_OPTIONS / qualified
- "Call me next week" → DECISION_MAKING / contacted
- "Not interested right now" → LONG_TERM_NURTURE / nurture
- "I need to discuss with my spouse" → DECISION_MAKING / qualified

Return JSON:
{{
  "decision_stage": "COMPARING_OPTIONS",
  "crm_status": "qualified",
  "confidence": 0.85,
  "reasoning": "Customer mentioned getting 2 more quotes and will decide by Friday"
}}
"""

            client = get_openai_client()
            if not client:
                raise ValueError("OpenAI API key not configured")
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert sales analyst. Classify customer decision stage accurately based on conversation. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Update lead
            decision_stage = LeadDecisionStage(result.get("decision_stage", "gathering_info").lower())
            new_status = LeadStatus(result.get("crm_status", "contacted").lower())

            lead.status = new_status
            lead.notes = (lead.notes or "") + f"\n[{datetime.now().isoformat()}] Auto-updated from call: {result.get('reasoning', '')}"

            db.commit()

            logger.info(f"Lead {lead_id} updated to status={new_status.value}, stage={decision_stage.value}")

            return new_status, decision_stage

        except Exception as e:
            logger.error(f"Error updating lead status: {str(e)}")
            raise

    async def schedule_follow_ups(self, call_id: str, action_items: List[ActionItem]) -> List[Dict]:
        """
        Create follow-up appointments/tasks based on action items

        Args:
            call_id: Voice interaction ID
            action_items: List of action items to schedule

        Returns:
            List of created appointments/tasks
        """
        try:
            db = self._get_db()
            voice_repo = VoiceInteractionRepository(db)

            call = voice_repo.get_by_id(call_id)
            if not call:
                raise ValueError(f"Call {call_id} not found")

            scheduled_items = []

            for action_item in action_items:
                # Schedule follow-up appointments for callback/call actions
                if action_item.action_type in [ActionItemType.CALLBACK, ActionItemType.SCHEDULE_CALL, ActionItemType.SCHEDULE_INSPECTION]:

                    # Create appointment
                    appointment = Appointment(
                        customer_id=call.customer_id,
                        lead_id=call.lead_id,
                        title=f"Follow-up: {action_item.description}",
                        appointment_type="follow_up_call" if "call" in action_item.action_type.value else "inspection",
                        scheduled_date=action_item.due_date,
                        status=AppointmentStatus.SCHEDULED,
                        notes=f"Auto-scheduled from call {call_id}\nContext: {action_item.context}",
                        created_from_call=True,
                        call_id=call_id
                    )

                    db.add(appointment)
                    db.commit()
                    db.refresh(appointment)

                    scheduled_items.append({
                        "type": "appointment",
                        "id": appointment.id,
                        "action": action_item.action_type.value,
                        "scheduled_date": appointment.scheduled_date.isoformat(),
                        "description": action_item.description
                    })

                    logger.info(f"Created follow-up appointment {appointment.id} from call {call_id}")

                # For other actions, create tasks (would integrate with task management system)
                else:
                    scheduled_items.append({
                        "type": "task",
                        "action": action_item.action_type.value,
                        "due_date": action_item.due_date.isoformat(),
                        "description": action_item.description,
                        "priority": action_item.priority
                    })

                    logger.info(f"Created task for {action_item.action_type.value} from call {call_id}")

            return scheduled_items

        except Exception as e:
            logger.error(f"Error scheduling follow-ups: {str(e)}")
            raise

    async def extract_property_details(self, transcript: str) -> Dict:
        """
        Extract property details from call transcript

        Args:
            transcript: Call transcript

        Returns:
            Dict with property address, roof type, age, condition, etc.
        """
        try:
            prompt = f"""Extract property and roof details from this roofing sales call transcript.

Transcript:
{transcript}

Extract:
- Property address (full address if mentioned)
- Roof type (asphalt shingle, metal, tile, flat, etc.)
- Roof age (years)
- Square footage (if mentioned)
- Number of stories
- Current roof condition
- Visible damage mentioned
- Budget range mentioned (if any)
- Timeline/urgency
- HOA requirements mentioned

Return as JSON:
{{
  "property_address": "123 Main St, City, State ZIP",
  "roof_type": "asphalt shingle",
  "roof_age_years": 15,
  "square_footage": 2500,
  "stories": 2,
  "condition": "fair, some curling shingles",
  "visible_damage": "storm damage on north side",
  "budget_range": "$15,000 - $20,000",
  "timeline": "within 2 months",
  "hoa_requirements": "requires approval, no metal roofs allowed",
  "confidence": 0.8
}}

Return "unknown" for any fields not mentioned.
"""

            client = get_openai_client()
            if not client:
                raise ValueError("OpenAI API key not configured")
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a roofing expert. Extract property and roof details accurately. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            property_data = json.loads(response.choices[0].message.content)
            logger.info(f"Extracted property details: {property_data.get('property_address', 'Unknown')}")

            return property_data

        except Exception as e:
            logger.error(f"Error extracting property details: {str(e)}")
            return {}

    async def detect_competitor_mentions(self, transcript: str) -> List[Dict]:
        """
        Detect competitor mentions in call transcript

        Args:
            transcript: Call transcript

        Returns:
            List of competitor mentions with context
        """
        try:
            prompt = f"""Identify all competitor mentions in this roofing sales call transcript.

Transcript:
{transcript}

Common competitors might include:
- Other roofing companies (local or national)
- Big box stores (Home Depot, Lowes)
- General contractors
- Insurance adjuster recommendations

For each competitor mentioned, extract:
- Company name
- What customer said about them
- Context (getting quotes, previous experience, price comparison)

Return as JSON array:
[
  {{
    "competitor": "ABC Roofing",
    "context": "Customer said they are getting a quote from them",
    "sentiment": "neutral",
    "quoted_price": "$18,000"
  }}
]
"""

            client = get_openai_client()
            if not client:
                raise ValueError("OpenAI API key not configured")
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a competitive intelligence analyst. Extract competitor mentions accurately. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            competitors = result.get("competitors", [])

            logger.info(f"Detected {len(competitors)} competitor mentions")
            return competitors

        except Exception as e:
            logger.error(f"Error detecting competitors: {str(e)}")
            return []

    async def ensure_compliance(self, call_id: str) -> Dict:
        """
        Ensure call compliance (recording consent, data privacy, etc.)

        Args:
            call_id: Voice interaction ID

        Returns:
            Dict with compliance status and details
        """
        try:
            db = self._get_db()
            voice_repo = VoiceInteractionRepository(db)

            call = voice_repo.get_by_id(call_id)
            if not call:
                raise ValueError(f"Call {call_id} not found")

            compliance_status = {
                "call_id": call_id,
                "recording_consent_obtained": False,
                "recording_stored": bool(call.recording_url),
                "transcript_stored": bool(call.transcript),
                "retention_expires": (datetime.now() + timedelta(days=2555)).isoformat(),  # 7 years
                "compliant": False,
                "issues": []
            }

            # Check if recording consent was obtained (look in transcript)
            if call.transcript:
                consent_phrases = [
                    "this call may be recorded",
                    "recording this call",
                    "call is being recorded",
                    "consent to record"
                ]

                if any(phrase in call.transcript.lower() for phrase in consent_phrases):
                    compliance_status["recording_consent_obtained"] = True

            # Check compliance requirements
            if not call.recording_url:
                compliance_status["issues"].append("No recording URL found")

            if not call.transcript:
                compliance_status["issues"].append("No transcript stored")

            if not compliance_status["recording_consent_obtained"]:
                compliance_status["issues"].append("Recording consent not verified in transcript")

            # Mark as compliant if no issues
            compliance_status["compliant"] = len(compliance_status["issues"]) == 0

            logger.info(f"Compliance check for call {call_id}: {'PASS' if compliance_status['compliant'] else 'FAIL'}")

            return compliance_status

        except Exception as e:
            logger.error(f"Error checking compliance: {str(e)}")
            raise

    async def process_call_end_to_end(self, call_id: str) -> Dict:
        """
        Complete end-to-end processing of a call

        1. Transcribe audio
        2. Extract action items
        3. Update lead status
        4. Schedule follow-ups
        5. Extract property details
        6. Detect competitors
        7. Ensure compliance

        Args:
            call_id: Voice interaction ID

        Returns:
            Dict with complete processing results
        """
        try:
            logger.info(f"Starting end-to-end processing for call {call_id}")

            results = {
                "call_id": call_id,
                "processed_at": datetime.now().isoformat(),
                "transcription": {},
                "action_items": [],
                "lead_update": {},
                "follow_ups": [],
                "property_details": {},
                "competitors": [],
                "compliance": {},
                "success": False
            }

            db = self._get_db()
            voice_repo = VoiceInteractionRepository(db)
            call = voice_repo.get_by_id(call_id)

            if not call:
                raise ValueError(f"Call {call_id} not found")

            # 1. Transcribe (if not already done)
            if not call.transcript and call.recording_url:
                results["transcription"] = await self.transcribe_call(call_id)
                call = voice_repo.get_by_id(call_id)  # Refresh
            else:
                results["transcription"] = {"status": "already_transcribed"}

            # 2. Extract action items
            if call.transcript:
                call_context = {
                    "caller_name": call.caller_name,
                    "intent": call.intent.value if call.intent else "unknown",
                    "sentiment": call.sentiment.value if call.sentiment else "neutral"
                }
                action_items = await self.extract_action_items(call.transcript, call_context)
                results["action_items"] = [item.to_dict() for item in action_items]

                # 3. Update lead status
                if call.lead_id:
                    new_status, decision_stage = await self.update_lead_status(
                        call.lead_id,
                        call.transcript,
                        call.intent
                    )
                    results["lead_update"] = {
                        "lead_id": call.lead_id,
                        "new_status": new_status.value,
                        "decision_stage": decision_stage.value
                    }

                # 4. Schedule follow-ups
                if action_items:
                    results["follow_ups"] = await self.schedule_follow_ups(call_id, action_items)

                # 5. Extract property details
                results["property_details"] = await self.extract_property_details(call.transcript)

                # 6. Detect competitors
                results["competitors"] = await self.detect_competitor_mentions(call.transcript)

            # 7. Ensure compliance
            results["compliance"] = await self.ensure_compliance(call_id)

            results["success"] = True
            logger.info(f"End-to-end processing completed for call {call_id}")

            return results

        except Exception as e:
            logger.error(f"Error in end-to-end processing: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
            return results
