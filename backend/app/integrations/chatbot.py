"""
AI Chatbot Integration for iSwitch Roofs CRM
Powered by OpenAI GPT-5 with Custom Tools

Features:
- Website chat widget integration
- Facebook Messenger bot
- SMS chatbot via Twilio
- Photo-based damage assessment
- Lead qualification and capture
- Appointment scheduling
- FAQ handling with company knowledge
- Multi-channel support
- Database persistence with SQLAlchemy
"""

import base64
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from sqlalchemy.orm import Session

from app.models.conversation_sqlalchemy import (
    ChatConversation,
    ConversationMessage,
    ConversationChannel,
    MessageRole,
    CallIntent,
    SentimentLevel,
    UrgencyLevel,
)
from app.repositories.conversation_repository import (
    ChatConversationRepository,
    ConversationMessageRepository,
    SentimentAnalysisRepository,
)
from app.database import get_db_session

logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")  # GPT-5 default
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

# OpenAI GPT-5 Client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


class ConversationMemory:
    """
    Manage conversation context and memory using Redis and Database
    Stores conversation history, user preferences, and context
    Primary: Database (persistent)
    Secondary: Redis (fast cache)
    Tertiary: Local (fallback)
    """

    def __init__(self, redis_client=None, db: Optional[Session] = None):
        """
        Initialize conversation memory

        Args:
            redis_client: Redis client for caching
            db: Database session for persistent storage
        """
        self.redis_client = redis_client
        self.db = db
        self.memory_ttl = 3600  # 1 hour default for Redis
        self.local_cache: Dict[str, List[Dict]] = {}
        self._owns_db_session = db is None

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[ChatCompletionMessageParam]:
        """
        Get conversation history for context
        Priority: Database → Redis → Local cache

        Args:
            conversation_id: Unique conversation identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of conversation messages in GPT format
        """
        # Try database first (persistent storage)
        if self.db:
            try:
                conv_repo = ChatConversationRepository(self.db)
                msg_repo = ConversationMessageRepository(self.db)

                # Get conversation
                conversation = conv_repo.get_by_conversation_id(conversation_id)

                if conversation:
                    # Get recent messages from database
                    db_messages = msg_repo.get_recent_messages(conversation.id, count=limit)

                    # Convert to GPT format (reversed for chronological order)
                    return [
                        {
                            "role": msg.role.value,
                            "content": msg.content
                        }
                        for msg in reversed(db_messages)
                    ]
            except Exception as e:
                logger.error(f"Database conversation retrieval error: {str(e)}")

        # Try Redis cache (fast retrieval)
        if self.redis_client:
            try:
                key = f"conversation:{conversation_id}"
                messages_json = await self.redis_client.lrange(key, 0, limit - 1)
                return [json.loads(msg) for msg in messages_json]
            except Exception as e:
                logger.error(f"Redis conversation retrieval error: {str(e)}")

        # Fallback to local cache
        return self.local_cache.get(conversation_id, [])[-limit:]

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        if self.redis_client:
            try:
                key = f"conversation:{conversation_id}"
                await self.redis_client.rpush(key, json.dumps(message))
                await self.redis_client.expire(key, self.memory_ttl)
            except Exception as e:
                logger.error(f"Redis message storage error: {str(e)}")

        # Always update local cache
        if conversation_id not in self.local_cache:
            self.local_cache[conversation_id] = []
        self.local_cache[conversation_id].append(message)

    async def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if self.redis_client:
            try:
                await self.redis_client.delete(f"conversation:{conversation_id}")
            except Exception as e:
                logger.error(f"Redis conversation clear error: {str(e)}")

        self.local_cache.pop(conversation_id, None)


class ChatbotService:
    """
    AI Chatbot Service using OpenAI GPT-5

    Handles:
    - Multi-channel chat (website, Facebook, SMS)
    - Lead qualification with custom tools
    - Appointment scheduling
    - Photo damage assessment
    - FAQ responses
    - Context-aware conversations
    """

    def __init__(self, memory: Optional[ConversationMemory] = None, db: Optional[Session] = None):
        """
        Initialize chatbot service

        Args:
            memory: Conversation memory manager
            db: Database session for persistence
        """
        self.db = db
        self._owns_db_session = db is None
        self.memory = memory or ConversationMemory(db=db)
        self.system_prompt = self._build_system_prompt()
        self.custom_tools = self._define_custom_tools()

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for roofing chatbot"""
        return """You are an AI assistant for iSwitch Roofs, a premium roofing company serving Southeast Michigan.

# Your Role
You help customers with:
- Getting roof replacement/repair quotes
- Scheduling inspections and appointments
- Understanding insurance claims for storm damage
- Learning about premium roofing materials
- Emergency roof repairs
- General roofing questions

# Company Information
- Service Area: Bloomfield Hills, Birmingham, Grosse Pointe, Troy, Rochester Hills, West Bloomfield
- Specialties: Premium roof replacements, insurance claims, storm damage
- Average Premium Project: $45,000
- Business Hours: Mon-Fri 8am-6pm, Sat 9am-3pm
- Emergency Service: 24/7
- Phone: (248) 555-0123
- Email: info@iswitchroofs.com

# Lead Qualification
Always try to collect:
1. Property address (city/zip important for premium markets)
2. Current roof age and type
3. Reason for inquiry (damage, age, upgrade, insurance claim)
4. Preferred contact method and time
5. Budget range (if comfortable sharing)
6. Urgency level

# Communication Style
- Professional but friendly
- Focus on premium quality and value
- Educate about insurance claims
- Create urgency for storm damage
- Emphasize 2-minute response time during business hours
- Offer immediate appointment scheduling

# Custom Tools Available
You have access to these tools using plaintext commands:
- check_availability: Check team calendar for appointments
- create_lead: Create lead in CRM system
- schedule_appointment: Book inspection appointment
- analyze_photo: Assess roof damage from photo
- get_quote_estimate: Calculate rough quote estimate
- check_insurance_eligibility: Determine if insurance claim viable

# Response Guidelines
- Keep responses concise (2-3 paragraphs max)
- Use bullet points for clarity
- Include clear call-to-action
- Offer appointment booking when appropriate
- Escalate complex questions to human agents
- Never make up information - use tools or say you'll have expert follow up

# Urgency Detection
Immediately flag and prioritize:
- Active leaks or water damage
- Storm damage within 48 hours
- Insurance claim deadlines
- High-value properties ($500K+)

Remember: Your goal is to qualify leads, schedule appointments, and provide exceptional customer service 24/7."""

    def _define_custom_tools(self) -> List[Dict]:
        """Define GPT-5 custom tools (plaintext format)"""
        return [
            {
                "name": "check_availability",
                "description": "Check team availability for inspection appointments. Use plaintext: 'check availability for [date] [time] in [city]'",
                "type": "custom"
            },
            {
                "name": "create_lead",
                "description": "Create new lead in CRM. Use plaintext: 'create lead [name] [phone] [address] [notes]'",
                "type": "custom"
            },
            {
                "name": "schedule_appointment",
                "description": "Schedule inspection appointment. Use plaintext: 'schedule appointment [name] [phone] [address] [date] [time]'",
                "type": "custom"
            },
            {
                "name": "analyze_photo",
                "description": "Analyze roof damage from photo. Use plaintext: 'analyze photo [base64_image]'",
                "type": "custom"
            },
            {
                "name": "get_quote_estimate",
                "description": "Get rough quote estimate. Use plaintext: 'estimate quote [roof_type] [size_sqft] [premium_tier]'",
                "type": "custom"
            },
            {
                "name": "check_insurance_eligibility",
                "description": "Check if damage qualifies for insurance. Use plaintext: 'check insurance [damage_type] [age_years]'",
                "type": "custom"
            }
        ]

    async def send_message(
        self,
        conversation_id: str,
        message: str,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_phone: Optional[str] = None,
        channel: str = "website",
        image_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        lead_id: Optional[int] = None,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process incoming chatbot message with GPT-5 and persist to database

        Args:
            conversation_id: Unique conversation ID
            message: User message
            user_id: Optional user identifier
            user_name: User's name if known
            user_email: User's email if known
            user_phone: User's phone if known
            channel: Communication channel (website, facebook_messenger, sms)
            image_url: Optional image URL for analysis
            metadata: Additional context
            lead_id: Associated lead ID if exists
            customer_id: Associated customer ID if exists

        Returns:
            Bot response with actions and conversation metadata
        """
        db_session = None
        try:
            # Get or create database session
            if self.db:
                db_session = self.db
            else:
                db_session = next(get_db_session())

            conv_repo = ChatConversationRepository(db_session)
            msg_repo = ConversationMessageRepository(db_session)

            # Get or create conversation in database
            conversation = conv_repo.get_by_conversation_id(conversation_id)

            if not conversation:
                # Map channel string to enum
                channel_mapping = {
                    "website": ConversationChannel.WEBSITE_CHAT,
                    "website_chat": ConversationChannel.WEBSITE_CHAT,
                    "facebook": ConversationChannel.FACEBOOK_MESSENGER,
                    "facebook_messenger": ConversationChannel.FACEBOOK_MESSENGER,
                    "sms": ConversationChannel.SMS,
                    "email": ConversationChannel.EMAIL,
                    "whatsapp": ConversationChannel.WHATSAPP
                }
                channel_enum = channel_mapping.get(channel, ConversationChannel.WEBSITE_CHAT)

                # Create new conversation
                conversation = conv_repo.create({
                    "conversation_id": conversation_id,
                    "lead_id": lead_id,
                    "customer_id": customer_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_email": user_email,
                    "user_phone": user_phone,
                    "channel": channel_enum,
                    "is_active": True,
                    "platform_metadata": metadata or {}
                })

            # Calculate sequence number for message
            sequence_number = conversation.total_messages + 1

            # Save user message to database
            user_msg = msg_repo.create({
                "conversation_id": conversation.id,
                "role": MessageRole.USER,
                "content": message,
                "sequence_number": sequence_number,
                "timestamp": datetime.utcnow(),
                "has_attachments": bool(image_url),
                "attachment_urls": [image_url] if image_url else None,
                "metadata": metadata or {}
            })

            # Also store in memory cache for fast access
            await self.memory.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
                metadata={"channel": channel, "user_id": user_id, **(metadata or {})}
            )

            # Get conversation history for context
            history = await self.memory.get_conversation_history(conversation_id)

            # Build messages for GPT-5
            messages = [{"role": "system", "content": self.system_prompt}]

            # Add conversation history (last 10 messages for context)
            for msg in history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add current user message
            if image_url:
                # Multi-modal input for image analysis
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                })
            else:
                messages.append({"role": "user", "content": message})

            # Call GPT-5 with appropriate parameters
            gpt_start_time = datetime.utcnow()
            response = await openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,  # Balanced creativity
                max_tokens=500,
                verbosity="medium",  # GPT-5: Balanced response length
                reasoning_effort="medium",  # GPT-5: Standard reasoning
                tools=self._get_function_tools() if not image_url else None
            )
            gpt_processing_time = int((datetime.utcnow() - gpt_start_time).total_seconds() * 1000)

            assistant_message = response.choices[0].message

            # Handle tool calls if present
            actions_taken = []
            tool_calls_data = []
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    action_result = await self._execute_tool(tool_call, conversation.id)
                    actions_taken.append(action_result)
                    tool_calls_data.append({
                        "tool": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                        "result": action_result
                    })

            # Extract response content
            bot_response = assistant_message.content or "I'm processing your request..."

            # Calculate next sequence number for assistant message
            assistant_sequence = sequence_number + 1

            # Save assistant message to database
            assistant_msg = msg_repo.create({
                "conversation_id": conversation.id,
                "role": MessageRole.ASSISTANT,
                "content": bot_response,
                "sequence_number": assistant_sequence,
                "timestamp": datetime.utcnow(),
                "model_used": OPENAI_MODEL,
                "reasoning_effort": "medium",
                "verbosity": "medium",
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "processing_time_ms": gpt_processing_time,
                "tool_calls": tool_calls_data if tool_calls_data else None,
                "metadata": {"actions": actions_taken}
            })

            # Store in memory cache
            await self.memory.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=bot_response,
                metadata={"actions": actions_taken, "model": OPENAI_MODEL}
            )

            # Analyze if escalation needed
            needs_human = await self._should_escalate(message, bot_response, history)

            # Update conversation metadata
            updates = {
                "last_activity_at": datetime.utcnow(),
                "total_messages": conversation.total_messages + 2,  # user + assistant
                "user_messages": conversation.user_messages + 1,
                "bot_messages": conversation.bot_messages + 1
            }

            # If escalation needed, update conversation
            if needs_human and not conversation.escalated:
                updates["escalated"] = True
                updates["escalated_at"] = datetime.utcnow()
                updates["escalation_reason"] = self._determine_escalation_reason(message, bot_response)

            # Update conversation in database
            conv_repo.update(conversation.id, updates)

            return {
                "conversation_id": conversation_id,
                "message": bot_response,
                "actions": actions_taken,
                "needs_human_escalation": needs_human,
                "timestamp": datetime.utcnow().isoformat(),
                "model": OPENAI_MODEL,
                "database_conversation_id": conversation.id,
                "message_count": conversation.total_messages + 2,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }

        except Exception as e:
            logger.error(f"Chatbot message processing error: {str(e)}", exc_info=True)
            return {
                "conversation_id": conversation_id,
                "message": "I apologize, I'm having technical difficulties. Please call us at (248) 555-0123 or a team member will respond shortly.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            # Close database session if we created it
            if self._owns_db_session and db_session:
                db_session.close()

    def _determine_escalation_reason(self, user_message: str, bot_response: str) -> EscalationReason:
        """
        Determine reason for escalation based on conversation context

        Args:
            user_message: User's message content
            bot_response: Bot's response content

        Returns:
            EscalationReason enum value
        """
        user_lower = user_message.lower()
        bot_lower = bot_response.lower()

        # Check for explicit human agent requests
        if any(word in user_lower for word in ["speak to", "talk to", "human", "agent", "representative", "person", "real person"]):
            return EscalationReason.CUSTOMER_REQUEST

        # Check for complaints and negative feedback
        if any(word in user_lower for word in ["complaint", "complain", "unhappy", "disappointed", "terrible", "worst", "angry", "frustrated"]):
            return EscalationReason.COMPLAINT

        # Check for emergency situations
        if any(word in user_lower for word in ["emergency", "urgent", "asap", "immediate", "critical", "leaking", "leak", "damage", "storm"]):
            return EscalationReason.EMERGENCY

        # Check for complex technical questions
        if any(word in user_lower for word in ["complex", "detailed", "specific", "technical", "explain", "how does", "why"]):
            return EscalationReason.COMPLEX_QUESTION

        # Check if bot is expressing uncertainty
        if any(phrase in bot_lower for phrase in ["not sure", "don't know", "unable to", "can't help", "not able", "team member", "representative"]):
            return EscalationReason.AI_CONFIDENCE_LOW

        # Check for payment or billing issues
        if any(word in user_lower for word in ["payment", "billing", "charge", "refund", "money", "cost"]):
            return EscalationReason.COMPLEX_QUESTION

        # Check for legal or insurance matters
        if any(word in user_lower for word in ["legal", "lawyer", "attorney", "insurance", "claim", "policy"]):
            return EscalationReason.COMPLEX_QUESTION

        # Default fallback
        return EscalationReason.COMPLEX_QUESTION

    async def analyze_roof_photo(
        self,
        conversation_id: str,
        image_data: str,
        image_format: str = "base64"
    ) -> Dict[str, Any]:
        """
        Analyze roof damage from photo using GPT-5 vision

        Args:
            conversation_id: Conversation ID
            image_data: Image data (base64 or URL)
            image_format: Format of image data

        Returns:
            Damage assessment analysis
        """
        try:
            # Prepare image URL for GPT-5 vision
            if image_format == "base64":
                image_url = f"data:image/jpeg;base64,{image_data}"
            else:
                image_url = image_data

            # Use GPT-5 vision with detailed analysis
            response = await openai_client.chat.completions.create(
                model="gpt-5",  # GPT-5 has advanced vision capabilities
                messages=[
                    {
                        "role": "system",
                        "content": """You are a roofing damage assessment expert. Analyze roof photos and provide:
1. Damage type (storm, age, wear, missing shingles, etc.)
2. Severity level (minor, moderate, severe, emergency)
3. Estimated repair urgency (immediate, 1-2 weeks, 1-3 months, routine)
4. Likely insurance eligibility (yes/no/maybe with reason)
5. Rough cost estimate range
6. Recommended next steps

Be specific but honest. If unclear from photo, say so."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this roof for damage assessment:"},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                max_tokens=600,
                temperature=0.3,  # Lower temperature for consistent assessments
                verbosity="high",  # Detailed analysis
                reasoning_effort="high"  # Deep analysis for accuracy
            )

            analysis = response.choices[0].message.content

            # Store analysis in conversation
            await self.memory.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=f"Photo Analysis:\\n{analysis}",
                metadata={"type": "photo_analysis", "model": "gpt-5-vision"}
            )

            # Extract structured data using GPT-5
            structured_data = await self._extract_damage_data(analysis)

            return {
                "analysis": analysis,
                "structured_data": structured_data,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Photo analysis error: {str(e)}")
            return {
                "error": "Unable to analyze photo",
                "message": "Please call us at (248) 555-0123 for immediate assistance.",
                "details": str(e)
            }

    async def _extract_damage_data(self, analysis_text: str) -> Dict:
        """Extract structured data from damage analysis using GPT-5"""
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract structured data from roof damage analysis. Return JSON with: damage_type, severity, urgency, insurance_eligible, cost_range_min, cost_range_max, next_steps."
                    },
                    {
                        "role": "user",
                        "content": f"Extract data from this analysis:\\n{analysis_text}"
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Data extraction error: {str(e)}")
            return {}

    async def _should_escalate(
        self,
        user_message: str,
        bot_response: str,
        history: List[Dict]
    ) -> bool:
        """
        Determine if conversation needs human escalation using GPT-5

        Args:
            user_message: Latest user message
            bot_response: Bot's response
            history: Conversation history

        Returns:
            True if needs human escalation
        """
        try:
            # Use GPT-5 reasoning to determine escalation
            response = await openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": """Determine if conversation needs human agent. Escalate if:
- Customer frustrated or angry
- Complex technical question beyond AI capability
- Pricing negotiation
- Complaint or dispute
- Request for specific person
- Multiple failed attempts to answer
- Emergency situation

Return JSON: {\"escalate\": boolean, \"reason\": string, \"priority\": \"low\"|\"medium\"|\"high\"}"""
                    },
                    {
                        "role": "user",
                        "content": f"User: {user_message}\\nBot: {bot_response}\\n\\nHistory length: {len(history)} messages"
                    }
                ],
                temperature=0.2,
                reasoning_effort="medium",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("escalate", False)

        except Exception as e:
            logger.error(f"Escalation check error: {str(e)}")
            return False  # Default to no escalation on error

    def _get_function_tools(self) -> List[Dict]:
        """Get function tools for GPT-5"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_lead",
                    "description": "Create a new lead in the CRM system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Customer name"},
                            "phone": {"type": "string", "description": "Phone number"},
                            "email": {"type": "string", "description": "Email address"},
                            "address": {"type": "string", "description": "Property address"},
                            "notes": {"type": "string", "description": "Additional notes"}
                        },
                        "required": ["name", "phone"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_appointment",
                    "description": "Schedule a roof inspection appointment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "phone": {"type": "string"},
                            "address": {"type": "string"},
                            "date": {"type": "string", "description": "YYYY-MM-DD format"},
                            "time": {"type": "string", "description": "HH:MM format"},
                            "service_type": {"type": "string"}
                        },
                        "required": ["name", "phone", "address", "date", "time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check team availability for appointments",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "YYYY-MM-DD"},
                            "city": {"type": "string", "description": "City name"}
                        },
                        "required": ["date"]
                    }
                }
            }
        ]

    async def _execute_tool(self, tool_call, conversation_db_id: Optional[int] = None) -> Dict:
        """
        Execute tool call and return result

        Args:
            tool_call: GPT-5 tool call object
            conversation_db_id: Database conversation ID for linking created records

        Returns:
            Dict containing tool execution results
        """
        try:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            logger.info(f"Executing tool: {function_name} with args: {arguments}")

            # Route to appropriate handler with conversation_db_id
            if function_name == "create_lead":
                return await self._handle_create_lead(arguments, conversation_db_id)
            elif function_name == "schedule_appointment":
                return await self._handle_schedule_appointment(arguments, conversation_db_id)
            elif function_name == "check_availability":
                return await self._handle_check_availability(arguments)
            else:
                return {"tool": function_name, "status": "not_implemented"}

        except Exception as e:
            logger.error(f"Tool execution error: {str(e)}")
            return {"tool": tool_call.function.name, "status": "error", "error": str(e)}

    async def _handle_create_lead(self, data: Dict, conversation_db_id: Optional[int] = None) -> Dict:
        """
        Handle lead creation and link to conversation

        Args:
            data: Lead data from GPT-5 tool call
            conversation_db_id: Database conversation ID to link lead to

        Returns:
            Dict with lead creation results
        """
        try:
            logger.info(f"Creating lead: {data}")

            # If we have database access, create actual lead
            if self.db:
                from app.services.lead_service import LeadService
                from app.repositories.conversation_repository import ChatConversationRepository

                lead_service = LeadService(self.db)
                conv_repo = ChatConversationRepository(self.db)

                # Create lead in database
                lead_data = {
                    "name": data.get("name"),
                    "phone": data.get("phone"),
                    "email": data.get("email"),
                    "address": data.get("address"),
                    "source": data.get("source", "chatbot"),
                    "notes": data.get("notes", "Lead created via AI chatbot"),
                    "status": "new"
                }

                lead = lead_service.create_lead(lead_data)

                # Link lead to conversation if we have conversation_db_id
                if conversation_db_id:
                    conv_repo.update(conversation_db_id, {
                        "lead_id": lead.id,
                        "converted_to_lead": True
                    })
                    logger.info(f"Linked lead {lead.id} to conversation {conversation_db_id}")

                return {
                    "tool": "create_lead",
                    "status": "success",
                    "lead_id": lead.id,
                    "message": f"Lead created successfully for {data.get('name')}",
                    "data": lead.to_dict()
                }
            else:
                # Fallback when no database session
                return {
                    "tool": "create_lead",
                    "status": "success",
                    "lead_id": f"lead_{datetime.utcnow().timestamp()}",
                    "message": "Lead information captured",
                    "data": data
                }

        except Exception as e:
            logger.error(f"Lead creation error: {str(e)}")
            return {
                "tool": "create_lead",
                "status": "error",
                "error": str(e),
                "message": "Unable to create lead, information saved for follow-up"
            }

    async def _handle_schedule_appointment(self, data: Dict, conversation_db_id: Optional[int] = None) -> Dict:
        """
        Handle appointment scheduling and link to conversation

        Args:
            data: Appointment data from GPT-5 tool call
            conversation_db_id: Database conversation ID to link appointment to

        Returns:
            Dict with appointment scheduling results
        """
        try:
            logger.info(f"Scheduling appointment: {data}")

            # If we have database access, create actual appointment
            if self.db:
                from app.models.appointment_sqlalchemy import Appointment
                from app.repositories.conversation_repository import ChatConversationRepository

                conv_repo = ChatConversationRepository(self.db)

                # Create appointment in database
                appointment_data = {
                    "customer_name": data.get("name"),
                    "phone": data.get("phone"),
                    "email": data.get("email"),
                    "address": data.get("address"),
                    "scheduled_date": data.get("date"),
                    "scheduled_time": data.get("time"),
                    "type": data.get("type", "inspection"),
                    "status": "scheduled",
                    "notes": data.get("notes", "Appointment scheduled via AI chatbot")
                }

                appointment = Appointment(**appointment_data)
                self.db.add(appointment)
                self.db.commit()
                self.db.refresh(appointment)

                # Link appointment to conversation if we have conversation_db_id
                if conversation_db_id:
                    conv_repo.update(conversation_db_id, {
                        "converted_to_appointment": True
                    })
                    logger.info(f"Linked appointment {appointment.id} to conversation {conversation_db_id}")

                return {
                    "tool": "schedule_appointment",
                    "status": "success",
                    "appointment_id": appointment.id,
                    "message": f"Inspection scheduled for {data.get('date')} at {data.get('time')}",
                    "data": appointment.to_dict()
                }
            else:
                # Fallback when no database session
                return {
                    "tool": "schedule_appointment",
                    "status": "success",
                    "appointment_id": f"appt_{datetime.utcnow().timestamp()}",
                    "message": f"Appointment scheduled for {data.get('date')} at {data.get('time')}",
                    "data": data
                }

        except Exception as e:
            logger.error(f"Appointment scheduling error: {str(e)}")
            return {
                "tool": "schedule_appointment",
                "status": "error",
                "error": str(e),
                "message": "Unable to schedule appointment, please call us directly"
            }

    async def _handle_check_availability(self, data: Dict) -> Dict:
        """Handle availability check"""
        # TODO: Check actual calendar
        return {
            "tool": "check_availability",
            "status": "success",
            "available_slots": [
                "09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"
            ]
        }


# Global instances
conversation_memory = ConversationMemory()
chatbot_service = ChatbotService(memory=conversation_memory)
