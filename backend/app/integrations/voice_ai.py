"""
AI Voice Assistant Integration for iSwitch Roofs CRM
Powered by Bland.ai + OpenAI GPT-5 for 24/7 inbound call handling

Features:
- Natural language understanding with GPT-5
- Appointment scheduling
- Lead qualification
- Intelligent transfer to humans
- Multi-language support (EN, ES)
- Real-time sentiment analysis
- Database persistence with SQLAlchemy
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import httpx
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.models.voice_interaction import (
    AppointmentBookingRequest,
    CallAnalysis,
    CallTransfer,
    ConversationFlow,
    VoiceConfiguration,
)
from app.models.conversation_sqlalchemy import (
    VoiceInteraction,
    CallIntent,
    CallOutcome,
    SentimentLevel,
    UrgencyLevel,
    EscalationReason,
)
from app.repositories.conversation_repository import (
    VoiceInteractionRepository,
    SentimentAnalysisRepository,
    ConversationQualityRepository,
)
from app.database import get_db_session

logger = logging.getLogger(__name__)

# Configuration
BLAND_AI_API_KEY = os.getenv("BLAND_AI_API_KEY")
BLAND_AI_BASE_URL = "https://api.bland.ai/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI GPT-5 Client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


class VoiceAIService:
    """
    AI Voice Assistant Service using Bland.ai + OpenAI GPT-5

    Handles:
    - Inbound call processing
    - Intent detection with GPT-5
    - Conversation management
    - Lead qualification
    - Appointment scheduling
    - Intelligent transfer to humans
    """

    def __init__(self, config: Optional[VoiceConfiguration] = None, db: Optional[Session] = None):
        """
        Initialize Voice AI service

        Args:
            config: Voice configuration settings
            db: Database session (optional, will create new if not provided)
        """
        self.config = config or VoiceConfiguration()
        self.client = httpx.AsyncClient(
            base_url=BLAND_AI_BASE_URL,
            headers={"Authorization": f"Bearer {BLAND_AI_API_KEY}"},
            timeout=30.0
        )
        self.conversation_flows: Dict[str, ConversationFlow] = {}
        self.db = db
        self._owns_db_session = db is None

    async def handle_inbound_call(
        self,
        phone_number: str,
        caller_name: Optional[str] = None,
        call_id: Optional[str] = None,
        lead_id: Optional[int] = None,
        customer_id: Optional[int] = None
    ) -> VoiceInteraction:
        """
        Handle incoming call with AI voice assistant and persist to database

        Args:
            phone_number: Caller's phone number
            caller_name: Caller's name if known
            call_id: Unique call identifier
            lead_id: Associated lead ID if known
            customer_id: Associated customer ID if known

        Returns:
            VoiceInteraction database object with complete call details
        """
        db_session = None
        try:
            # Get or create database session
            if self.db:
                db_session = self.db
            else:
                db_session = next(get_db_session())

            repo = VoiceInteractionRepository(db_session)
            sentiment_repo = SentimentAnalysisRepository(db_session)

            # Initialize conversation flow
            flow_id = call_id or f"call_{datetime.utcnow().timestamp()}"
            flow = ConversationFlow(
                flow_id=flow_id,
                current_step="greeting",
                collected_data={
                    "phone_number": phone_number,
                    "caller_name": caller_name,
                    "lead_id": lead_id,
                    "customer_id": customer_id
                }
            )
            self.conversation_flows[flow_id] = flow

            call_started_at = datetime.utcnow()

            # Determine greeting based on time
            greeting = self._get_greeting_message()

            # Start call with Bland.ai
            call_response = await self._initiate_bland_call(
                phone_number=phone_number,
                greeting=greeting,
                flow_id=flow_id
            )

            bland_call_id = call_response.get("id")
            transcript = call_response.get("transcript", "")
            call_duration = call_response.get("duration", 0)
            call_ended_at = datetime.utcnow()

            # Process conversation with GPT-5
            processed_transcript, intent, intent_confidence = await self._process_conversation_gpt5(
                transcript,
                flow
            )

            # Generate summary and analyze sentiment
            summary = await self._generate_summary_gpt5(processed_transcript)
            sentiment_result = await self._analyze_sentiment_detailed(processed_transcript)

            # Determine outcome and urgency
            outcome = await self._determine_outcome(flow, intent)
            urgency_score = self._calculate_urgency(intent, sentiment_result)

            # Extract key information from flow
            collected_data = flow.collected_data
            appointment_scheduled = outcome == CallOutcome.APPOINTMENT_SCHEDULED
            appointment_date = collected_data.get("appointment_date")
            escalated = flow.requires_human

            # Create voice interaction record in database
            interaction_data = {
                "bland_call_id": bland_call_id,
                "lead_id": lead_id or collected_data.get("lead_id"),
                "customer_id": customer_id or collected_data.get("customer_id"),
                "phone_number": phone_number,
                "caller_name": caller_name,
                "call_duration_seconds": call_duration,
                "call_started_at": call_started_at,
                "call_ended_at": call_ended_at,
                "intent": intent,
                "intent_confidence": intent_confidence,
                "outcome": outcome,
                "transcript": processed_transcript,
                "summary": summary,
                "key_phrases": sentiment_result.get("key_phrases", []),
                "sentiment": sentiment_result.get("sentiment_level"),
                "sentiment_score": sentiment_result.get("sentiment_score"),
                "sentiment_confidence": sentiment_result.get("confidence"),
                "emotions": sentiment_result.get("emotions"),
                "urgency_level": self._score_to_urgency_level(urgency_score),
                "urgency_score": urgency_score,
                "qualification_score": flow.context.get("qualification_score", 0.0),
                "buying_signals": sentiment_result.get("buying_signals", []),
                "pain_points": sentiment_result.get("pain_points", []),
                "collected_data": collected_data,
                "address_collected": collected_data.get("address"),
                "roof_age_years": collected_data.get("roof_age"),
                "project_budget": collected_data.get("budget"),
                "timeline_preference": collected_data.get("timeline"),
                "insurance_claim": collected_data.get("insurance_claim", False),
                "appointment_scheduled": appointment_scheduled,
                "appointment_date": appointment_date,
                "appointment_type": collected_data.get("appointment_type"),
                "escalated_to_human": escalated,
                "escalation_reason": EscalationReason.AI_CONFIDENCE_LOW if escalated and intent_confidence < 0.7 else None,
                "escalation_timestamp": datetime.utcnow() if escalated else None,
                "follow_up_required": self._requires_followup(outcome, intent),
                "recording_url": call_response.get("recording_url"),
                "call_metadata": {
                    "flow_id": flow_id,
                    "bland_call_id": bland_call_id,
                    "flow_steps": flow.completed_steps,
                    "context": flow.context
                },
                "gpt5_model_version": "gpt-5"
            }

            # Save to database
            interaction = repo.create(interaction_data)

            # Create sentiment analysis record
            if sentiment_result:
                sentiment_data = {
                    "voice_interaction_id": interaction.id,
                    "analysis_type": "conversation",
                    "sentiment_level": sentiment_result.get("sentiment_level"),
                    "sentiment_score": sentiment_result.get("sentiment_score", 0.0),
                    "confidence_score": sentiment_result.get("confidence", 0.0),
                    "primary_emotion": sentiment_result.get("primary_emotion"),
                    "emotions": sentiment_result.get("emotions", {}),
                    "urgency_level": self._score_to_urgency_level(urgency_score),
                    "urgency_score": urgency_score,
                    "urgency_indicators": sentiment_result.get("urgency_indicators", []),
                    "buying_signals": sentiment_result.get("buying_signals", []),
                    "buying_signal_strength": len(sentiment_result.get("buying_signals", [])) / 10.0,
                    "pain_points": sentiment_result.get("pain_points", []),
                    "concerns": sentiment_result.get("concerns", []),
                    "alert_triggered": sentiment_result.get("sentiment_score", 0.0) < -0.5 or urgency_score >= 8.0,
                    "alert_severity": "high" if urgency_score >= 8.0 else "medium" if urgency_score >= 6.0 else "low",
                    "model_used": "gpt-5",
                    "analyzed_text_length": len(processed_transcript)
                }
                sentiment_repo.create(sentiment_data)

            logger.info(
                f"Call completed and saved to database: {interaction.id} "
                f"(Bland ID: {bland_call_id}) - Intent: {intent.value} - Outcome: {outcome.value}"
            )

            return interaction

        except Exception as e:
            logger.error(f"Error handling inbound call: {str(e)}", exc_info=True)
            raise
        finally:
            # Close database session if we created it
            if self._owns_db_session and db_session:
                db_session.close()

    async def _process_conversation_gpt5(
        self,
        transcript: str,
        flow: ConversationFlow
    ) -> Tuple[str, CallIntent, float]:
        """
        Process conversation using GPT-5 for intent detection and next steps

        Args:
            transcript: Call transcript
            flow: Current conversation flow

        Returns:
            Tuple of (processed_transcript, detected_intent, confidence_score)
        """
        try:
            # Build context-aware system prompt
            system_prompt = self._build_system_prompt(flow)

            # Call GPT-5 with reasoning for intent detection
            response = await openai_client.chat.completions.create(
                model="gpt-5",  # Latest GPT-5 model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this call transcript and determine intent:\\n\\n{transcript}"}
                ],
                temperature=0.3,  # Lower temperature for consistent intent detection
                verbosity="medium",  # New GPT-5 parameter for balanced responses
                reasoning_effort="high",  # Use high reasoning for accurate intent detection
                response_format={"type": "json_object"}
            )

            # Parse GPT-5 response
            result = json.loads(response.choices[0].message.content)

            intent_str = result.get("intent", "unknown").lower()
            confidence = float(result.get("confidence", 0.5))

            # Map string to CallIntent enum
            intent_mapping = {
                "quote": CallIntent.QUOTE_REQUEST,
                "appointment": CallIntent.APPOINTMENT_SCHEDULE,
                "question": CallIntent.QUESTION_INQUIRY,
                "emergency": CallIntent.EMERGENCY_SERVICE,
                "status": CallIntent.STATUS_UPDATE,
                "complaint": CallIntent.COMPLAINT,
                "callback": CallIntent.CALLBACK_REQUEST
            }

            intent = intent_mapping.get(intent_str, CallIntent.UNKNOWN)

            # Update conversation flow
            flow.collected_data.update(result.get("collected_data", {}))
            flow.context.update(result.get("context", {}))

            return transcript, intent, confidence

        except Exception as e:
            logger.error(f"GPT-5 conversation processing error: {str(e)}")
            return transcript, CallIntent.UNKNOWN, 0.5

    async def _generate_summary_gpt5(self, transcript: str) -> str:
        """
        Generate concise call summary using GPT-5

        Args:
            transcript: Call transcript

        Returns:
            Concise summary of call
        """
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a roofing CRM assistant. Summarize call transcripts in 2-3 sentences focusing on customer needs and next actions."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this roofing service call:\\n\\n{transcript}"
                    }
                ],
                max_tokens=150,
                temperature=0.5,
                verbosity="low"  # Request concise output
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            return "Call summary unavailable"

    async def _analyze_sentiment_gpt5(self, transcript: str) -> SentimentScore:
        """
        Analyze customer sentiment using GPT-5

        Args:
            transcript: Call transcript

        Returns:
            Sentiment classification
        """
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze customer sentiment from call transcripts. Return JSON with 'sentiment' (very_positive, positive, neutral, negative, very_negative) and 'confidence' (0-1)."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze sentiment:\\n\\n{transcript}"
                    }
                ],
                temperature=0.2,
                reasoning_effort="medium",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            sentiment_str = result.get("sentiment", "neutral")

            sentiment_mapping = {
                "very_positive": SentimentScore.VERY_POSITIVE,
                "positive": SentimentScore.POSITIVE,
                "neutral": SentimentScore.NEUTRAL,
                "negative": SentimentScore.NEGATIVE,
                "very_negative": SentimentScore.VERY_NEGATIVE
            }

            return sentiment_mapping.get(sentiment_str, SentimentScore.NEUTRAL)

        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return SentimentScore.NEUTRAL

    async def analyze_call_quality(
        self,
        interaction_id: str,
        transcript: str,
        duration_seconds: int
    ) -> CallAnalysis:
        """
        Perform detailed call quality analysis using GPT-5

        Args:
            interaction_id: Interaction ID
            transcript: Call transcript
            duration_seconds: Call duration

        Returns:
            Detailed call analysis
        """
        try:
            # Use GPT-5 with high reasoning for comprehensive analysis
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert roofing sales analyst. Analyze call transcripts and provide:
                        1. Intent and confidence
                        2. Sentiment and confidence
                        3. Key phrases (important customer statements)
                        4. Questions asked by customer
                        5. Objections raised
                        6. Buying signals detected
                        7. Urgency score (0-10)
                        8. Lead qualification score (0-100)
                        9. Recommended next action
                        10. Concise summary

                        Return JSON format."""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this {duration_seconds}s roofing call:\\n\\n{transcript}"
                    }
                ],
                temperature=0.3,
                verbosity="high",  # Detailed analysis
                reasoning_effort="high",  # Deep analysis
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Map to CallAnalysis model
            analysis = CallAnalysis(
                interaction_id=interaction_id,
                duration_seconds=duration_seconds,
                intent=CallIntent(result.get("intent", "unknown")),
                intent_confidence=float(result.get("intent_confidence", 0.5)),
                sentiment=SentimentScore(result.get("sentiment", "neutral")),
                sentiment_confidence=float(result.get("sentiment_confidence", 0.5)),
                key_phrases=result.get("key_phrases", []),
                questions_asked=result.get("questions_asked", []),
                objections=result.get("objections", []),
                buying_signals=result.get("buying_signals", []),
                urgency_score=float(result.get("urgency_score", 5.0)),
                qualification_score=float(result.get("qualification_score", 50.0)),
                next_best_action=result.get("next_best_action", "Follow up within 24 hours"),
                summary=result.get("summary", "")
            )

            return analysis

        except Exception as e:
            logger.error(f"Call quality analysis error: {str(e)}")
            raise

    async def schedule_appointment_from_call(
        self,
        booking_request: AppointmentBookingRequest,
        flow_id: str
    ) -> Dict:
        """
        Schedule appointment from voice interaction

        Args:
            booking_request: Appointment details
            flow_id: Conversation flow ID

        Returns:
            Created appointment data
        """
        try:
            # Validate booking request using GPT-5
            validation_result = await self._validate_appointment_gpt5(booking_request)

            if not validation_result["valid"]:
                logger.warning(f"Invalid appointment request: {validation_result['reason']}")
                return {"error": validation_result["reason"]}

            # Create appointment in CRM (would call actual CRM API)
            appointment_data = {
                "customer_name": booking_request.caller_name,
                "phone": booking_request.phone_number,
                "email": booking_request.email,
                "property_address": booking_request.property_address,
                "scheduled_date": booking_request.preferred_date,
                "scheduled_time": booking_request.preferred_time,
                "service_type": booking_request.service_type,
                "notes": booking_request.notes,
                "urgency": booking_request.urgency,
                "source": "voice_ai",
                "flow_id": flow_id
            }

            # Update conversation flow
            if flow_id in self.conversation_flows:
                self.conversation_flows[flow_id].collected_data["appointment"] = appointment_data
                self.conversation_flows[flow_id].completed_steps.append("appointment_scheduled")

            logger.info(f"Appointment scheduled via voice AI: {flow_id}")
            return {"success": True, "appointment": appointment_data}

        except Exception as e:
            logger.error(f"Appointment scheduling error: {str(e)}")
            return {"error": str(e)}

    async def _validate_appointment_gpt5(self, request: AppointmentBookingRequest) -> Dict:
        """Validate appointment request using GPT-5"""
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "Validate appointment requests. Check for valid date, time, address, and contact info. Return JSON with 'valid' (boolean) and 'reason' (if invalid)."
                    },
                    {
                        "role": "user",
                        "content": f"Validate this appointment:\\n{request.model_dump_json()}"
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Appointment validation error: {str(e)}")
            return {"valid": True, "reason": ""}  # Default to valid on error

    async def should_transfer_to_human(
        self,
        flow: ConversationFlow,
        transcript: str
    ) -> Tuple[bool, str]:
        """
        Determine if call should be transferred to human using GPT-5 reasoning

        Args:
            flow: Conversation flow
            transcript: Current transcript

        Returns:
            Tuple of (should_transfer, reason)
        """
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze if roofing call needs human transfer. Transfer if:
                        - Complex technical questions
                        - Customer frustration/anger
                        - High-value project (>$50K)
                        - Emergency situation
                        - Multiple objections
                        - Specific agent request

                        Return JSON: {\"transfer\": boolean, \"reason\": string, \"priority\": \"low\"|\"medium\"|\"high\"}"""
                    },
                    {
                        "role": "user",
                        "content": f"Should this call transfer to human?\\n\\nTranscript:\\n{transcript}\\n\\nContext: {json.dumps(flow.context)}"
                    }
                ],
                temperature=0.2,
                reasoning_effort="high",  # Deep reasoning for transfer decisions
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            should_transfer = result.get("transfer", False)
            reason = result.get("reason", "AI can continue")

            if should_transfer:
                flow.requires_human = True
                flow.transfer_reason = reason

            return should_transfer, reason

        except Exception as e:
            logger.error(f"Transfer decision error: {str(e)}")
            return False, ""

    def _build_system_prompt(self, flow: ConversationFlow) -> str:
        """Build context-aware system prompt for GPT-5"""
        base_prompt = """You are an AI assistant for iSwitch Roofs, a premium roofing company.

Your role:
- Understand customer needs professionally
- Qualify leads by gathering: property details, roof age, damage type, budget, urgency
- Schedule appointments when requested
- Answer basic questions about services
- Detect intent and collect relevant information
- Maintain friendly, helpful tone

Current step: {step}
Collected data: {data}

Analyze the conversation and return JSON with:
{{
  \"intent\": \"quote|appointment|question|emergency|status|complaint|callback\",
  \"confidence\": 0-1,
  \"collected_data\": {{...new data collected...}},
  \"context\": {{...important context...}},
  \"next_action\": \"suggested next step\"
}}"""

        return base_prompt.format(
            step=flow.current_step,
            data=json.dumps(flow.collected_data)
        )

    def _get_greeting_message(self) -> str:
        """Get appropriate greeting based on time"""
        current_hour = datetime.now().hour

        if 8 <= current_hour < 18:
            return self.config.business_hours_greeting
        else:
            return self.config.after_hours_greeting

    async def _initiate_bland_call(
        self,
        phone_number: str,
        greeting: str,
        flow_id: str
    ) -> Dict:
        """Initiate call with Bland.ai API"""
        try:
            response = await self.client.post(
                "/calls",
                json={
                    "phone_number": phone_number,
                    "task": greeting,
                    "voice": self.config.voice_id,
                    "language": self.config.language,
                    "max_duration": self.config.max_call_duration_minutes * 60,
                    "record": self.config.enable_recording,
                    "transcribe": self.config.enable_transcription,
                    "metadata": {"flow_id": flow_id}
                }
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Bland.ai call initiation error: {str(e)}")
            raise

    async def _determine_outcome(self, flow: ConversationFlow, intent: CallIntent) -> Optional[CallOutcome]:
        """Determine call outcome based on flow and intent"""
        if flow.requires_human:
            return CallOutcome.TRANSFERRED_TO_HUMAN
        elif "lead_id" in flow.collected_data:
            return CallOutcome.LEAD_CREATED
        elif "appointment" in flow.collected_data:
            return CallOutcome.APPOINTMENT_SCHEDULED
        elif intent == CallIntent.QUESTION_INQUIRY:
            return CallOutcome.QUESTION_ANSWERED
        else:
            return CallOutcome.NO_ACTION_NEEDED

    async def _analyze_sentiment_detailed(self, transcript: str) -> Dict:
        """
        Perform detailed sentiment analysis using GPT-5

        Args:
            transcript: Call transcript

        Returns:
            Dictionary with comprehensive sentiment analysis
        """
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze roofing service call sentiment in detail.
                        Return JSON with:
                        - sentiment_level: very_negative, negative, neutral, positive, very_positive
                        - sentiment_score: -1.0 to 1.0
                        - confidence: 0.0 to 1.0
                        - primary_emotion: main emotion detected
                        - emotions: {emotion: intensity} dict
                        - key_phrases: important phrases from call
                        - buying_signals: list of buying indicators
                        - pain_points: customer problems mentioned
                        - concerns: customer worries or objections
                        - urgency_indicators: signs of urgency"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this roofing call:\n\n{transcript}"
                    }
                ],
                temperature=0.2,
                reasoning_effort="high",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Map sentiment_level string to enum
            sentiment_str = result.get("sentiment_level", "neutral")
            sentiment_mapping = {
                "very_negative": SentimentLevel.VERY_NEGATIVE,
                "negative": SentimentLevel.NEGATIVE,
                "neutral": SentimentLevel.NEUTRAL,
                "positive": SentimentLevel.POSITIVE,
                "very_positive": SentimentLevel.VERY_POSITIVE
            }
            result["sentiment_level"] = sentiment_mapping.get(sentiment_str, SentimentLevel.NEUTRAL)

            return result

        except Exception as e:
            logger.error(f"Detailed sentiment analysis error: {str(e)}")
            return {
                "sentiment_level": SentimentLevel.NEUTRAL,
                "sentiment_score": 0.0,
                "confidence": 0.5,
                "primary_emotion": "neutral",
                "emotions": {},
                "key_phrases": [],
                "buying_signals": [],
                "pain_points": [],
                "concerns": [],
                "urgency_indicators": []
            }

    def _calculate_urgency(self, intent: CallIntent, sentiment_result: Dict) -> float:
        """
        Calculate urgency score (0.0 to 10.0) based on intent and sentiment

        Args:
            intent: Detected call intent
            sentiment_result: Sentiment analysis results

        Returns:
            Urgency score from 0.0 (low) to 10.0 (critical)
        """
        # Base urgency by intent
        intent_urgency = {
            CallIntent.EMERGENCY_SERVICE: 9.0,
            CallIntent.COMPLAINT: 7.0,
            CallIntent.INSURANCE_CLAIM: 6.5,
            CallIntent.QUOTE_REQUEST: 5.0,
            CallIntent.APPOINTMENT_SCHEDULE: 5.5,
            CallIntent.STATUS_UPDATE: 4.0,
            CallIntent.QUESTION_INQUIRY: 3.0,
            CallIntent.CALLBACK_REQUEST: 4.5
        }

        base_score = intent_urgency.get(intent, 3.0)

        # Adjust based on sentiment (negative sentiment increases urgency)
        sentiment_score = sentiment_result.get("sentiment_score", 0.0)
        if sentiment_score < -0.5:
            base_score += 2.0  # Very negative
        elif sentiment_score < 0:
            base_score += 1.0  # Negative

        # Adjust based on urgency indicators
        urgency_indicators = sentiment_result.get("urgency_indicators", [])
        base_score += min(len(urgency_indicators) * 0.5, 2.0)

        # Cap at 10.0
        return min(base_score, 10.0)

    def _score_to_urgency_level(self, score: float) -> UrgencyLevel:
        """
        Convert urgency score to UrgencyLevel enum

        Args:
            score: Urgency score from 0.0 to 10.0

        Returns:
            UrgencyLevel enum value
        """
        if score >= 8.0:
            return UrgencyLevel.CRITICAL
        elif score >= 6.0:
            return UrgencyLevel.HIGH
        elif score >= 4.0:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _requires_followup(self, outcome: CallOutcome, intent: CallIntent) -> bool:
        """
        Determine if call requires follow-up

        Args:
            outcome: Call outcome
            intent: Call intent

        Returns:
            True if follow-up is required
        """
        # Always follow up on these outcomes
        followup_outcomes = {
            CallOutcome.CALLBACK_REQUESTED,
            CallOutcome.TRANSFERRED_TO_HUMAN,
            CallOutcome.VOICEMAIL,
            CallOutcome.COMPLAINT_LOGGED,
            CallOutcome.EMERGENCY_DISPATCHED
        }

        if outcome in followup_outcomes:
            return True

        # Follow up on high-priority intents with no action
        if outcome == CallOutcome.NO_ACTION_NEEDED and intent in {
            CallIntent.EMERGENCY_SERVICE,
            CallIntent.COMPLAINT,
            CallIntent.INSURANCE_CLAIM
        }:
            return True

        return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
voice_ai_service = VoiceAIService()
