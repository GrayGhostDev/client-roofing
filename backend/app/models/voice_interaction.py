"""
Voice Interaction Models for AI Voice Assistant
Supports Bland.ai integration for 24/7 inbound call handling
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CallIntent(str, Enum):
    """Call intent types"""
    QUOTE_REQUEST = "quote_request"
    APPOINTMENT_SCHEDULE = "appointment_schedule"
    QUESTION_INQUIRY = "question_inquiry"
    EMERGENCY_SERVICE = "emergency_service"
    STATUS_UPDATE = "status_update"
    COMPLAINT = "complaint"
    CALLBACK_REQUEST = "callback_request"
    UNKNOWN = "unknown"


class CallStatus(str, Enum):
    """Call status types"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TRANSFERRED = "transferred"
    FAILED = "failed"
    MISSED = "missed"


class CallOutcome(str, Enum):
    """Call outcome types"""
    LEAD_CREATED = "lead_created"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    QUESTION_ANSWERED = "question_answered"
    TRANSFERRED_TO_HUMAN = "transferred_to_human"
    VOICEMAIL_LEFT = "voicemail_left"
    NO_ACTION_NEEDED = "no_action_needed"


class SentimentScore(str, Enum):
    """Sentiment classifications"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class VoiceInteractionCreate(BaseModel):
    """Schema for creating a voice interaction"""
    phone_number: str = Field(..., description="Caller's phone number")
    caller_name: Optional[str] = Field(None, description="Caller's name if provided")
    call_duration_seconds: int = Field(..., ge=0, description="Call duration in seconds")
    intent: CallIntent = Field(..., description="Detected call intent")
    status: CallStatus = Field(default=CallStatus.INITIATED, description="Current call status")
    outcome: Optional[CallOutcome] = Field(None, description="Call outcome")
    transcript: Optional[str] = Field(None, description="Full call transcript")
    summary: Optional[str] = Field(None, description="AI-generated call summary")
    sentiment_score: Optional[SentimentScore] = Field(None, description="Overall sentiment")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in intent detection")
    lead_id: Optional[str] = Field(None, description="Created/updated lead ID")
    appointment_id: Optional[str] = Field(None, description="Created appointment ID")
    transferred_to_agent: Optional[str] = Field(None, description="Agent ID if transferred")
    recording_url: Optional[str] = Field(None, description="Call recording URL")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+1-248-555-0123",
                "caller_name": "John Smith",
                "call_duration_seconds": 180,
                "intent": "appointment_schedule",
                "status": "completed",
                "outcome": "appointment_scheduled",
                "transcript": "Caller requested appointment for roof inspection...",
                "summary": "Customer wants roof inspection for storm damage. Scheduled for Oct 15 at 2pm.",
                "sentiment_score": "positive",
                "confidence_score": 0.92,
                "lead_id": "lead_abc123",
                "appointment_id": "appt_xyz789"
            }
        }


class VoiceInteractionResponse(BaseModel):
    """Response schema for voice interaction"""
    id: str
    phone_number: str
    caller_name: Optional[str]
    call_duration_seconds: int
    intent: CallIntent
    status: CallStatus
    outcome: Optional[CallOutcome]
    transcript: Optional[str]
    summary: Optional[str]
    sentiment_score: Optional[SentimentScore]
    confidence_score: float
    lead_id: Optional[str]
    appointment_id: Optional[str]
    transferred_to_agent: Optional[str]
    recording_url: Optional[str]
    metadata: Dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CallAnalysis(BaseModel):
    """Detailed call analysis results"""
    interaction_id: str
    duration_seconds: int
    intent: CallIntent
    intent_confidence: float = Field(..., ge=0.0, le=1.0)
    sentiment: SentimentScore
    sentiment_confidence: float = Field(..., ge=0.0, le=1.0)
    key_phrases: List[str] = Field(default_factory=list, description="Important phrases detected")
    questions_asked: List[str] = Field(default_factory=list, description="Questions caller asked")
    objections: List[str] = Field(default_factory=list, description="Customer objections")
    buying_signals: List[str] = Field(default_factory=list, description="Buying intent signals")
    urgency_score: float = Field(..., ge=0.0, le=10.0, description="Urgency level 0-10")
    qualification_score: float = Field(..., ge=0.0, le=100.0, description="Lead quality score")
    next_best_action: str = Field(..., description="Recommended next action")
    summary: str = Field(..., description="Concise call summary")


class ConversationFlow(BaseModel):
    """Conversation flow state"""
    flow_id: str = Field(..., description="Unique flow identifier")
    current_step: str = Field(..., description="Current step in conversation")
    completed_steps: List[str] = Field(default_factory=list, description="Completed steps")
    collected_data: Dict = Field(default_factory=dict, description="Data collected during conversation")
    context: Dict = Field(default_factory=dict, description="Conversation context")
    requires_human: bool = Field(default=False, description="Whether human transfer is needed")
    transfer_reason: Optional[str] = Field(None, description="Reason for human transfer")


class AppointmentBookingRequest(BaseModel):
    """Appointment booking request from voice interaction"""
    caller_name: str = Field(..., description="Customer name")
    phone_number: str = Field(..., description="Contact phone")
    email: Optional[str] = Field(None, description="Contact email")
    property_address: str = Field(..., description="Property address")
    preferred_date: str = Field(..., description="Preferred date (YYYY-MM-DD)")
    preferred_time: str = Field(..., description="Preferred time (HH:MM)")
    service_type: str = Field(..., description="Type of service requested")
    notes: Optional[str] = Field(None, description="Additional notes")
    urgency: str = Field(default="normal", description="Urgency level")


class CallTransfer(BaseModel):
    """Call transfer request"""
    interaction_id: str
    agent_id: Optional[str] = Field(None, description="Specific agent to transfer to")
    department: str = Field(..., description="Department to transfer to")
    reason: str = Field(..., description="Reason for transfer")
    context_summary: str = Field(..., description="Summary for agent")
    customer_sentiment: SentimentScore
    priority: str = Field(default="normal", description="Priority level")


class VoiceAnalytics(BaseModel):
    """Voice interaction analytics"""
    total_calls: int
    average_duration_seconds: float
    intent_distribution: Dict[CallIntent, int]
    outcome_distribution: Dict[CallOutcome, int]
    sentiment_distribution: Dict[SentimentScore, int]
    transfer_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of calls transferred")
    automation_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage handled by AI")
    average_confidence_score: float
    leads_created: int
    appointments_scheduled: int
    after_hours_calls: int
    missed_calls: int
    customer_satisfaction: Optional[float] = Field(None, ge=0.0, le=5.0, description="Average CSAT score")


class VoiceConfiguration(BaseModel):
    """Voice AI configuration"""
    provider: str = Field(default="bland_ai", description="Voice AI provider")
    voice_id: str = Field(default="professional-male-v1", description="Voice type")
    language: str = Field(default="en-US", description="Primary language")
    secondary_languages: List[str] = Field(default_factory=list, description="Additional languages")
    max_call_duration_minutes: int = Field(default=15, ge=1, le=60, description="Max call duration")
    transfer_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0,
                                                   description="Confidence threshold for transfer")
    enable_recording: bool = Field(default=True, description="Enable call recording")
    enable_transcription: bool = Field(default=True, description="Enable transcription")
    enable_sentiment_analysis: bool = Field(default=True, description="Enable sentiment analysis")
    business_hours_start: str = Field(default="08:00", description="Business hours start (HH:MM)")
    business_hours_end: str = Field(default="18:00", description="Business hours end (HH:MM)")
    after_hours_greeting: str = Field(
        default="Thank you for calling iSwitch Roofs. We're currently closed but I'm here to help you 24/7.",
        description="After-hours greeting message"
    )
    business_hours_greeting: str = Field(
        default="Thank you for calling iSwitch Roofs. How can I help you today?",
        description="Business hours greeting message"
    )
