"""
Conversation Database Models (SQLAlchemy)
Complete implementation for voice interactions, chatbot conversations, and analytics
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum as SQLEnum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

from app.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class CallIntent(enum.Enum):
    """Call intent classification"""
    QUOTE_REQUEST = "quote_request"
    APPOINTMENT_SCHEDULE = "appointment_schedule"
    QUESTION_INQUIRY = "question_inquiry"
    EMERGENCY_SERVICE = "emergency_service"
    INSURANCE_CLAIM = "insurance_claim"
    STATUS_UPDATE = "status_update"
    COMPLAINT = "complaint"
    REFERRAL = "referral"
    OTHER = "other"


class CallOutcome(enum.Enum):
    """Call outcome classification"""
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    QUOTE_PROVIDED = "quote_provided"
    INFORMATION_PROVIDED = "information_provided"
    TRANSFERRED_TO_HUMAN = "transferred_to_human"
    VOICEMAIL = "voicemail"
    CALLBACK_REQUESTED = "callback_requested"
    NO_ACTION_NEEDED = "no_action_needed"
    COMPLAINT_LOGGED = "complaint_logged"
    EMERGENCY_DISPATCHED = "emergency_dispatched"


class SentimentLevel(enum.Enum):
    """Sentiment classification levels"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class UrgencyLevel(enum.Enum):
    """Urgency classification levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConversationChannel(enum.Enum):
    """Conversation channel types"""
    VOICE = "voice"
    WEBSITE_CHAT = "website_chat"
    FACEBOOK_MESSENGER = "facebook_messenger"
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class MessageRole(enum.Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class EscalationReason(enum.Enum):
    """Reason for escalation to human agent"""
    COMPLEX_QUESTION = "complex_question"
    CUSTOMER_REQUEST = "customer_request"
    TECHNICAL_ISSUE = "technical_issue"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    HIGH_VALUE_OPPORTUNITY = "high_value_opportunity"
    COMPLAINT = "complaint"
    EMERGENCY = "emergency"
    AI_CONFIDENCE_LOW = "ai_confidence_low"


# ============================================================================
# VOICE INTERACTION MODEL
# ============================================================================

class VoiceInteraction(Base):
    """
    Voice interaction database model
    Stores all voice call interactions with AI assistant
    """
    __tablename__ = "voice_interactions"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # External IDs
    bland_call_id = Column(String(255), unique=True, nullable=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)

    # Call Details
    phone_number = Column(String(20), nullable=False, index=True)
    caller_name = Column(String(255), nullable=True)
    call_duration_seconds = Column(Integer, nullable=False, default=0)
    call_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    call_ended_at = Column(DateTime, nullable=True)

    # Intent and Classification
    intent = Column(SQLEnum(CallIntent), nullable=False, index=True)
    intent_confidence = Column(Float, nullable=False, default=0.0)
    outcome = Column(SQLEnum(CallOutcome), nullable=True, index=True)

    # Conversation Content
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    key_phrases = Column(JSON, nullable=True)  # List[str]

    # Sentiment Analysis
    sentiment = Column(SQLEnum(SentimentLevel), nullable=True, index=True)
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_confidence = Column(Float, nullable=True)
    emotions = Column(JSON, nullable=True)  # Dict[str, float]

    # Lead Qualification
    urgency_level = Column(SQLEnum(UrgencyLevel), nullable=True, index=True)
    urgency_score = Column(Float, nullable=True)  # 0.0 to 10.0
    qualification_score = Column(Float, nullable=True)  # 0.0 to 100.0
    buying_signals = Column(JSON, nullable=True)  # List[str]
    pain_points = Column(JSON, nullable=True)  # List[str]

    # Data Collection
    collected_data = Column(JSON, nullable=True)  # Dict[str, Any]
    address_collected = Column(String(500), nullable=True)
    roof_age_years = Column(Integer, nullable=True)
    project_budget = Column(Float, nullable=True)
    timeline_preference = Column(String(100), nullable=True)
    insurance_claim = Column(Boolean, nullable=True, default=False)

    # Appointment Scheduling
    appointment_scheduled = Column(Boolean, nullable=False, default=False)
    appointment_date = Column(DateTime, nullable=True)
    appointment_type = Column(String(100), nullable=True)

    # Escalation
    escalated_to_human = Column(Boolean, nullable=False, default=False, index=True)
    escalation_reason = Column(SQLEnum(EscalationReason), nullable=True)
    escalation_timestamp = Column(DateTime, nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)

    # Quality Metrics
    quality_score = Column(Float, nullable=True)  # 0.0 to 100.0
    quality_dimensions = Column(JSON, nullable=True)  # Dict with professionalism, clarity, etc.
    ai_performance_rating = Column(Float, nullable=True)  # 0.0 to 5.0

    # Follow-up
    follow_up_required = Column(Boolean, nullable=False, default=False)
    follow_up_notes = Column(Text, nullable=True)
    follow_up_completed = Column(Boolean, nullable=False, default=False)
    follow_up_completed_at = Column(DateTime, nullable=True)

    # Recording and Metadata
    recording_url = Column(String(500), nullable=True)
    call_metadata = Column(JSON, nullable=True)
    gpt5_model_version = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="voice_interactions", foreign_keys=[lead_id])
    customer = relationship("Customer", back_populates="voice_interactions", foreign_keys=[customer_id])
    assigned_agent = relationship("TeamMember", foreign_keys=[assigned_agent_id])
    quality_analyses = relationship("ConversationQuality", back_populates="voice_interaction", cascade="all, delete-orphan")
    sentiment_analyses = relationship("SentimentAnalysis", back_populates="voice_interaction", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("ix_voice_call_started", "call_started_at"),
        Index("ix_voice_phone_created", "phone_number", "created_at"),
        Index("ix_voice_intent_outcome", "intent", "outcome"),
        Index("ix_voice_escalated", "escalated_to_human", "escalation_timestamp"),
        CheckConstraint("call_duration_seconds >= 0", name="check_call_duration_positive"),
        CheckConstraint("sentiment_score >= -1.0 AND sentiment_score <= 1.0", name="check_sentiment_score_range"),
        CheckConstraint("urgency_score >= 0.0 AND urgency_score <= 10.0", name="check_urgency_score_range"),
        CheckConstraint("qualification_score >= 0.0 AND qualification_score <= 100.0", name="check_qualification_score_range"),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "bland_call_id": self.bland_call_id,
            "lead_id": self.lead_id,
            "customer_id": self.customer_id,
            "phone_number": self.phone_number,
            "caller_name": self.caller_name,
            "call_duration_seconds": self.call_duration_seconds,
            "call_started_at": self.call_started_at.isoformat() if self.call_started_at else None,
            "call_ended_at": self.call_ended_at.isoformat() if self.call_ended_at else None,
            "intent": self.intent.value if self.intent else None,
            "intent_confidence": self.intent_confidence,
            "outcome": self.outcome.value if self.outcome else None,
            "transcript": self.transcript,
            "summary": self.summary,
            "key_phrases": self.key_phrases,
            "sentiment": self.sentiment.value if self.sentiment else None,
            "sentiment_score": self.sentiment_score,
            "urgency_level": self.urgency_level.value if self.urgency_level else None,
            "urgency_score": self.urgency_score,
            "qualification_score": self.qualification_score,
            "collected_data": self.collected_data,
            "appointment_scheduled": self.appointment_scheduled,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "escalated_to_human": self.escalated_to_human,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# CHAT CONVERSATION MODEL
# ============================================================================

class ChatConversation(Base):
    """
    Chat conversation database model
    Stores chatbot conversations across multiple channels
    """
    __tablename__ = "chat_conversations"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(255), unique=True, nullable=False, index=True)

    # External IDs
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)

    # User Information
    user_id = Column(String(255), nullable=True, index=True)
    user_name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    user_phone = Column(String(20), nullable=True)

    # Channel and Platform
    channel = Column(SQLEnum(ConversationChannel), nullable=False, index=True)
    platform_metadata = Column(JSON, nullable=True)

    # Conversation State
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolution_notes = Column(Text, nullable=True)

    # Intent and Classification
    primary_intent = Column(SQLEnum(CallIntent), nullable=True, index=True)
    intent_confidence = Column(Float, nullable=True)
    detected_intents = Column(JSON, nullable=True)  # List[Dict] - all detected intents

    # Sentiment Tracking
    current_sentiment = Column(SQLEnum(SentimentLevel), nullable=True, index=True)
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_trend = Column(String(20), nullable=True)  # "improving", "declining", "stable"

    # Lead Qualification
    qualification_score = Column(Float, nullable=True)  # 0.0 to 100.0
    urgency_score = Column(Float, nullable=True)  # 0.0 to 10.0
    buying_signals = Column(JSON, nullable=True)  # List[str]

    # Collected Data
    collected_data = Column(JSON, nullable=True)  # Dict[str, Any]
    address = Column(String(500), nullable=True)
    roof_age = Column(Integer, nullable=True)
    project_type = Column(String(100), nullable=True)

    # Escalation
    escalated = Column(Boolean, nullable=False, default=False, index=True)
    escalation_reason = Column(SQLEnum(EscalationReason), nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)

    # Conversation Metrics
    total_messages = Column(Integer, nullable=False, default=0)
    user_messages = Column(Integer, nullable=False, default=0)
    bot_messages = Column(Integer, nullable=False, default=0)
    total_duration_seconds = Column(Integer, nullable=True)
    average_response_time_seconds = Column(Float, nullable=True)

    # Quality Metrics
    quality_score = Column(Float, nullable=True)  # 0.0 to 100.0
    customer_satisfaction_score = Column(Integer, nullable=True)  # 1-5 CSAT
    nps_score = Column(Integer, nullable=True)  # -100 to 100

    # Photo Analysis
    photos_uploaded = Column(Integer, nullable=False, default=0)
    photo_analysis_results = Column(JSON, nullable=True)  # List[Dict]

    # Conversion Tracking
    converted_to_lead = Column(Boolean, nullable=False, default=False)
    converted_to_appointment = Column(Boolean, nullable=False, default=False)
    conversion_value = Column(Float, nullable=True)

    # Session Management
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_activity_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True)
    session_duration_seconds = Column(Integer, nullable=True)

    # AI Configuration
    gpt5_model_version = Column(String(50), nullable=True)
    ai_configuration = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="chat_conversations", foreign_keys=[lead_id])
    customer = relationship("Customer", back_populates="chat_conversations", foreign_keys=[customer_id])
    assigned_agent = relationship("TeamMember", foreign_keys=[assigned_agent_id])
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.timestamp.asc()")
    quality_analyses = relationship("ConversationQuality", back_populates="chat_conversation", cascade="all, delete-orphan")
    sentiment_analyses = relationship("SentimentAnalysis", back_populates="chat_conversation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_chat_channel_active", "channel", "is_active"),
        Index("ix_chat_started_channel", "started_at", "channel"),
        Index("ix_chat_user_id", "user_id"),
        Index("ix_chat_escalated", "escalated", "escalated_at"),
        CheckConstraint("sentiment_score >= -1.0 AND sentiment_score <= 1.0", name="check_chat_sentiment_range"),
        CheckConstraint("qualification_score >= 0.0 AND qualification_score <= 100.0", name="check_chat_qualification_range"),
        CheckConstraint("urgency_score >= 0.0 AND urgency_score <= 10.0", name="check_chat_urgency_range"),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "lead_id": self.lead_id,
            "customer_id": self.customer_id,
            "user_name": self.user_name,
            "channel": self.channel.value if self.channel else None,
            "is_active": self.is_active,
            "is_resolved": self.is_resolved,
            "primary_intent": self.primary_intent.value if self.primary_intent else None,
            "current_sentiment": self.current_sentiment.value if self.current_sentiment else None,
            "sentiment_score": self.sentiment_score,
            "qualification_score": self.qualification_score,
            "total_messages": self.total_messages,
            "escalated": self.escalated,
            "converted_to_lead": self.converted_to_lead,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# CONVERSATION MESSAGE MODEL
# ============================================================================

class ConversationMessage(Base):
    """
    Individual message in a chat conversation
    """
    __tablename__ = "conversation_messages"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False, index=True)

    # Message Content
    role = Column(SQLEnum(MessageRole), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, default="text")  # text, image, file, etc.

    # Message Metadata
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    sequence_number = Column(Integer, nullable=False)

    # AI-Specific Fields
    model_used = Column(String(50), nullable=True)
    reasoning_effort = Column(String(20), nullable=True)
    verbosity = Column(String(20), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Tool Calls (for assistant messages)
    tool_calls = Column(JSON, nullable=True)  # List[Dict]
    tool_call_results = Column(JSON, nullable=True)  # List[Dict]

    # Sentiment (for user messages)
    sentiment = Column(SQLEnum(SentimentLevel), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    emotions = Column(JSON, nullable=True)  # Dict[str, float]

    # Intent (for user messages)
    detected_intent = Column(String(100), nullable=True)
    intent_confidence = Column(Float, nullable=True)

    # Image/File Attachments
    has_attachments = Column(Boolean, nullable=False, default=False)
    attachment_urls = Column(JSON, nullable=True)  # List[str]
    attachment_metadata = Column(JSON, nullable=True)

    # Buying Signals
    contains_buying_signal = Column(Boolean, nullable=False, default=False)
    buying_signals = Column(JSON, nullable=True)  # List[str]

    # Quality Indicators
    message_quality_score = Column(Float, nullable=True)
    is_coherent = Column(Boolean, nullable=True)
    is_relevant = Column(Boolean, nullable=True)

    # Metadata (renamed to avoid SQLAlchemy reserved word)
    message_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("ix_msg_conversation_timestamp", "conversation_id", "timestamp"),
        Index("ix_msg_conversation_sequence", "conversation_id", "sequence_number"),
        Index("ix_msg_role_timestamp", "role", "timestamp"),
        CheckConstraint("sentiment_score >= -1.0 AND sentiment_score <= 1.0", name="check_msg_sentiment_range"),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role.value if self.role else None,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sequence_number": self.sequence_number,
            "sentiment": self.sentiment.value if self.sentiment else None,
            "sentiment_score": self.sentiment_score,
            "detected_intent": self.detected_intent,
            "has_attachments": self.has_attachments,
            "contains_buying_signal": self.contains_buying_signal,
        }


# ============================================================================
# SENTIMENT ANALYSIS MODEL
# ============================================================================

class SentimentAnalysis(Base):
    """
    Detailed sentiment analysis results for conversations
    """
    __tablename__ = "sentiment_analyses"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys (one of these will be set)
    voice_interaction_id = Column(Integer, ForeignKey("voice_interactions.id"), nullable=True, index=True)
    chat_conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=True, index=True)
    message_id = Column(Integer, ForeignKey("conversation_messages.id"), nullable=True, index=True)

    # Analysis Type
    analysis_type = Column(String(50), nullable=False)  # "message", "conversation", "thread"
    analysis_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Sentiment Results
    sentiment_level = Column(SQLEnum(SentimentLevel), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0

    # Emotional Analysis
    primary_emotion = Column(String(50), nullable=True)
    emotions = Column(JSON, nullable=False)  # Dict[str, float] - joy, anger, fear, etc.
    emotional_intensity = Column(Float, nullable=True)  # 0.0 to 1.0

    # Urgency Analysis
    urgency_level = Column(SQLEnum(UrgencyLevel), nullable=False, index=True)
    urgency_score = Column(Float, nullable=False)  # 0.0 to 10.0
    urgency_indicators = Column(JSON, nullable=True)  # List[str]

    # Intent and Signals
    buying_signals = Column(JSON, nullable=True)  # List[str]
    buying_signal_strength = Column(Float, nullable=True)  # 0.0 to 1.0
    pain_points = Column(JSON, nullable=True)  # List[str]
    concerns = Column(JSON, nullable=True)  # List[str]

    # Sentiment Trends (for thread analysis)
    sentiment_trend = Column(String(20), nullable=True)  # "improving", "declining", "stable"
    sentiment_volatility = Column(Float, nullable=True)  # 0.0 to 1.0
    trend_data = Column(JSON, nullable=True)  # List of sentiment scores over time

    # Alert Triggers
    alert_triggered = Column(Boolean, nullable=False, default=False, index=True)
    alert_reason = Column(String(100), nullable=True)
    alert_severity = Column(String(20), nullable=True)  # "low", "medium", "high", "critical"

    # Customer Satisfaction Indicators
    satisfaction_indicators = Column(JSON, nullable=True)  # List[str]
    dissatisfaction_indicators = Column(JSON, nullable=True)  # List[str]

    # AI Model Info
    model_used = Column(String(50), nullable=False)
    model_version = Column(String(50), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Additional Context
    analyzed_text_length = Column(Integer, nullable=True)
    context_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    voice_interaction = relationship("VoiceInteraction", back_populates="sentiment_analyses")
    chat_conversation = relationship("ChatConversation", back_populates="sentiment_analyses")

    # Indexes
    __table_args__ = (
        Index("ix_sentiment_voice_timestamp", "voice_interaction_id", "analysis_timestamp"),
        Index("ix_sentiment_chat_timestamp", "chat_conversation_id", "analysis_timestamp"),
        Index("ix_sentiment_level_timestamp", "sentiment_level", "analysis_timestamp"),
        Index("ix_sentiment_alert", "alert_triggered", "alert_severity"),
        CheckConstraint("sentiment_score >= -1.0 AND sentiment_score <= 1.0", name="check_sentiment_analysis_score_range"),
        CheckConstraint("urgency_score >= 0.0 AND urgency_score <= 10.0", name="check_sentiment_urgency_range"),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "voice_interaction_id": self.voice_interaction_id,
            "chat_conversation_id": self.chat_conversation_id,
            "analysis_type": self.analysis_type,
            "sentiment_level": self.sentiment_level.value if self.sentiment_level else None,
            "sentiment_score": self.sentiment_score,
            "confidence_score": self.confidence_score,
            "primary_emotion": self.primary_emotion,
            "emotions": self.emotions,
            "urgency_level": self.urgency_level.value if self.urgency_level else None,
            "urgency_score": self.urgency_score,
            "buying_signals": self.buying_signals,
            "alert_triggered": self.alert_triggered,
            "analysis_timestamp": self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
        }


# ============================================================================
# CONVERSATION QUALITY MODEL
# ============================================================================

class ConversationQuality(Base):
    """
    Conversation quality analysis and scoring
    """
    __tablename__ = "conversation_quality"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys (one of these will be set)
    voice_interaction_id = Column(Integer, ForeignKey("voice_interactions.id"), nullable=True, index=True)
    chat_conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=True, index=True)

    # Analysis Metadata
    analysis_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    analyzed_by = Column(String(50), nullable=False)  # "gpt-5", "human", etc.

    # Overall Quality
    overall_score = Column(Float, nullable=False)  # 0.0 to 100.0
    quality_grade = Column(String(2), nullable=False)  # A+, A, B+, B, C+, C, D, F

    # Quality Dimensions (each 0-100)
    professionalism_score = Column(Float, nullable=False)
    professionalism_notes = Column(Text, nullable=True)

    responsiveness_score = Column(Float, nullable=False)
    responsiveness_notes = Column(Text, nullable=True)

    clarity_score = Column(Float, nullable=False)
    clarity_notes = Column(Text, nullable=True)

    helpfulness_score = Column(Float, nullable=False)
    helpfulness_notes = Column(Text, nullable=True)

    resolution_score = Column(Float, nullable=False)
    resolution_notes = Column(Text, nullable=True)

    # Additional Quality Metrics
    accuracy_score = Column(Float, nullable=True)
    empathy_score = Column(Float, nullable=True)
    efficiency_score = Column(Float, nullable=True)

    # Strengths and Weaknesses
    strengths = Column(JSON, nullable=True)  # List[str]
    weaknesses = Column(JSON, nullable=True)  # List[str]
    improvement_opportunities = Column(JSON, nullable=True)  # List[str]

    # Compliance and Best Practices
    followed_best_practices = Column(Boolean, nullable=True)
    compliance_issues = Column(JSON, nullable=True)  # List[str]

    # Customer Experience
    customer_effort_score = Column(Float, nullable=True)  # 1.0 to 7.0 (CES)
    customer_satisfaction_score = Column(Integer, nullable=True)  # 1 to 5 (CSAT)
    net_promoter_score = Column(Integer, nullable=True)  # -100 to 100 (NPS)

    # AI Performance (for bot conversations)
    ai_accuracy = Column(Float, nullable=True)
    ai_relevance = Column(Float, nullable=True)
    ai_coherence = Column(Float, nullable=True)
    ai_mistakes = Column(JSON, nullable=True)  # List[str]

    # Conversation Metrics
    total_turns = Column(Integer, nullable=True)
    average_response_time = Column(Float, nullable=True)
    conversation_duration_seconds = Column(Integer, nullable=True)

    # Issue Detection
    issues_detected = Column(Boolean, nullable=False, default=False)
    issue_types = Column(JSON, nullable=True)  # List[str]
    issue_severity = Column(String(20), nullable=True)

    # Training Recommendations
    training_needed = Column(Boolean, nullable=False, default=False)
    training_topics = Column(JSON, nullable=True)  # List[str]

    # Detailed Analysis
    full_analysis = Column(JSON, nullable=True)  # Complete GPT-5 analysis

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    voice_interaction = relationship("VoiceInteraction", back_populates="quality_analyses")
    chat_conversation = relationship("ChatConversation", back_populates="quality_analyses")

    # Indexes
    __table_args__ = (
        Index("ix_quality_voice_timestamp", "voice_interaction_id", "analysis_timestamp"),
        Index("ix_quality_chat_timestamp", "chat_conversation_id", "analysis_timestamp"),
        Index("ix_quality_overall_score", "overall_score"),
        Index("ix_quality_grade", "quality_grade"),
        CheckConstraint("overall_score >= 0.0 AND overall_score <= 100.0", name="check_quality_overall_score"),
        CheckConstraint("professionalism_score >= 0.0 AND professionalism_score <= 100.0", name="check_quality_professionalism"),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "voice_interaction_id": self.voice_interaction_id,
            "chat_conversation_id": self.chat_conversation_id,
            "overall_score": self.overall_score,
            "quality_grade": self.quality_grade,
            "professionalism_score": self.professionalism_score,
            "responsiveness_score": self.responsiveness_score,
            "clarity_score": self.clarity_score,
            "helpfulness_score": self.helpfulness_score,
            "resolution_score": self.resolution_score,
            "strengths": self.strengths,
            "improvement_opportunities": self.improvement_opportunities,
            "analysis_timestamp": self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
        }
