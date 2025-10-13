"""
Conversation Repository Classes
Complete data access layer for conversation AI features
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.conversation_sqlalchemy import (
    VoiceInteraction, ChatConversation, ConversationMessage,
    SentimentAnalysis, ConversationQuality,
    CallIntent, CallOutcome, SentimentLevel, UrgencyLevel,
    ConversationChannel, MessageRole, EscalationReason
)


class VoiceInteractionRepository:
    """Repository for voice interaction data access"""

    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def create(self, interaction_data: Dict) -> VoiceInteraction:
        """
        Create new voice interaction

        Args:
            interaction_data: Dictionary of interaction attributes

        Returns:
            Created VoiceInteraction object
        """
        interaction = VoiceInteraction(**interaction_data)
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def get_by_id(self, interaction_id: int) -> Optional[VoiceInteraction]:
        """Get voice interaction by ID"""
        return self.db.query(VoiceInteraction).filter(
            VoiceInteraction.id == interaction_id,
            VoiceInteraction.deleted_at.is_(None)
        ).first()

    def get_by_bland_call_id(self, bland_call_id: str) -> Optional[VoiceInteraction]:
        """Get voice interaction by Bland.ai call ID"""
        return self.db.query(VoiceInteraction).filter(
            VoiceInteraction.bland_call_id == bland_call_id,
            VoiceInteraction.deleted_at.is_(None)
        ).first()

    def get_by_phone_number(
        self,
        phone_number: str,
        limit: int = 10
    ) -> List[VoiceInteraction]:
        """Get recent voice interactions for a phone number"""
        return self.db.query(VoiceInteraction).filter(
            VoiceInteraction.phone_number == phone_number,
            VoiceInteraction.deleted_at.is_(None)
        ).order_by(
            desc(VoiceInteraction.call_started_at)
        ).limit(limit).all()

    def get_by_lead(self, lead_id: int) -> List[VoiceInteraction]:
        """Get all voice interactions for a lead"""
        return self.db.query(VoiceInteraction).filter(
            VoiceInteraction.lead_id == lead_id,
            VoiceInteraction.deleted_at.is_(None)
        ).order_by(
            desc(VoiceInteraction.call_started_at)
        ).all()

    def get_escalated_calls(
        self,
        since: Optional[datetime] = None
    ) -> List[VoiceInteraction]:
        """Get escalated calls that need human attention"""
        query = self.db.query(VoiceInteraction).filter(
            VoiceInteraction.escalated_to_human == True,
            VoiceInteraction.deleted_at.is_(None)
        )

        if since:
            query = query.filter(VoiceInteraction.escalation_timestamp >= since)

        return query.order_by(
            desc(VoiceInteraction.escalation_timestamp)
        ).all()

    def get_calls_needing_followup(self) -> List[VoiceInteraction]:
        """Get calls that need follow-up but not yet completed"""
        return self.db.query(VoiceInteraction).filter(
            VoiceInteraction.follow_up_required == True,
            VoiceInteraction.follow_up_completed == False,
            VoiceInteraction.deleted_at.is_(None)
        ).order_by(
            desc(VoiceInteraction.created_at)
        ).all()

    def get_calls_by_intent(
        self,
        intent: CallIntent,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[VoiceInteraction]:
        """Get calls filtered by intent and date range"""
        query = self.db.query(VoiceInteraction).filter(
            VoiceInteraction.intent == intent,
            VoiceInteraction.deleted_at.is_(None)
        )

        if start_date:
            query = query.filter(VoiceInteraction.call_started_at >= start_date)
        if end_date:
            query = query.filter(VoiceInteraction.call_started_at <= end_date)

        return query.order_by(
            desc(VoiceInteraction.call_started_at)
        ).all()

    def get_high_urgency_calls(
        self,
        min_urgency_score: float = 7.0,
        since: Optional[datetime] = None
    ) -> List[VoiceInteraction]:
        """Get high urgency calls"""
        query = self.db.query(VoiceInteraction).filter(
            VoiceInteraction.urgency_score >= min_urgency_score,
            VoiceInteraction.deleted_at.is_(None)
        )

        if since:
            query = query.filter(VoiceInteraction.call_started_at >= since)

        return query.order_by(
            desc(VoiceInteraction.urgency_score)
        ).all()

    def get_qualified_leads(
        self,
        min_qualification_score: float = 70.0,
        limit: int = 50
    ) -> List[VoiceInteraction]:
        """Get highly qualified lead calls"""
        return self.db.query(VoiceInteraction).filter(
            VoiceInteraction.qualification_score >= min_qualification_score,
            VoiceInteraction.deleted_at.is_(None)
        ).order_by(
            desc(VoiceInteraction.qualification_score)
        ).limit(limit).all()

    def update(self, interaction_id: int, updates: Dict) -> Optional[VoiceInteraction]:
        """Update voice interaction"""
        interaction = self.get_by_id(interaction_id)
        if not interaction:
            return None

        for key, value in updates.items():
            if hasattr(interaction, key):
                setattr(interaction, key, value)

        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def soft_delete(self, interaction_id: int) -> bool:
        """Soft delete voice interaction"""
        interaction = self.get_by_id(interaction_id)
        if not interaction:
            return False

        interaction.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get voice interaction statistics"""
        query = self.db.query(VoiceInteraction).filter(
            VoiceInteraction.deleted_at.is_(None)
        )

        if start_date:
            query = query.filter(VoiceInteraction.call_started_at >= start_date)
        if end_date:
            query = query.filter(VoiceInteraction.call_started_at <= end_date)

        total_calls = query.count()

        # Calculate averages
        avg_duration = self.db.query(
            func.avg(VoiceInteraction.call_duration_seconds)
        ).filter(
            VoiceInteraction.deleted_at.is_(None)
        ).scalar() or 0

        avg_quality = self.db.query(
            func.avg(VoiceInteraction.quality_score)
        ).filter(
            VoiceInteraction.deleted_at.is_(None),
            VoiceInteraction.quality_score.isnot(None)
        ).scalar() or 0

        # Count by outcome
        outcomes = self.db.query(
            VoiceInteraction.outcome,
            func.count(VoiceInteraction.id)
        ).filter(
            VoiceInteraction.deleted_at.is_(None)
        ).group_by(
            VoiceInteraction.outcome
        ).all()

        # Escalation rate
        escalated_count = query.filter(
            VoiceInteraction.escalated_to_human == True
        ).count()

        # Appointment rate
        appointment_count = query.filter(
            VoiceInteraction.appointment_scheduled == True
        ).count()

        return {
            "total_calls": total_calls,
            "average_duration_seconds": float(avg_duration),
            "average_quality_score": float(avg_quality),
            "outcomes": {str(outcome): count for outcome, count in outcomes},
            "escalation_rate": (escalated_count / total_calls * 100) if total_calls > 0 else 0,
            "appointment_rate": (appointment_count / total_calls * 100) if total_calls > 0 else 0,
            "escalated_count": escalated_count,
            "appointment_count": appointment_count
        }


class ChatConversationRepository:
    """Repository for chat conversation data access"""

    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def create(self, conversation_data: Dict) -> ChatConversation:
        """Create new chat conversation"""
        conversation = ChatConversation(**conversation_data)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: int) -> Optional[ChatConversation]:
        """Get chat conversation by ID with messages"""
        return self.db.query(ChatConversation).options(
            joinedload(ChatConversation.messages)
        ).filter(
            ChatConversation.id == conversation_id,
            ChatConversation.deleted_at.is_(None)
        ).first()

    def get_by_conversation_id(self, conversation_id: str) -> Optional[ChatConversation]:
        """Get chat conversation by conversation_id string"""
        return self.db.query(ChatConversation).options(
            joinedload(ChatConversation.messages)
        ).filter(
            ChatConversation.conversation_id == conversation_id,
            ChatConversation.deleted_at.is_(None)
        ).first()

    def get_by_user(self, user_id: str, limit: int = 10) -> List[ChatConversation]:
        """Get recent conversations for a user"""
        return self.db.query(ChatConversation).filter(
            ChatConversation.user_id == user_id,
            ChatConversation.deleted_at.is_(None)
        ).order_by(
            desc(ChatConversation.last_activity_at)
        ).limit(limit).all()

    def get_active_conversations(
        self,
        channel: Optional[ConversationChannel] = None
    ) -> List[ChatConversation]:
        """Get all active conversations"""
        query = self.db.query(ChatConversation).filter(
            ChatConversation.is_active == True,
            ChatConversation.deleted_at.is_(None)
        )

        if channel:
            query = query.filter(ChatConversation.channel == channel)

        return query.order_by(
            desc(ChatConversation.last_activity_at)
        ).all()

    def get_escalated_conversations(self) -> List[ChatConversation]:
        """Get conversations escalated to humans"""
        return self.db.query(ChatConversation).filter(
            ChatConversation.escalated == True,
            ChatConversation.is_resolved == False,
            ChatConversation.deleted_at.is_(None)
        ).order_by(
            desc(ChatConversation.escalated_at)
        ).all()

    def get_by_sentiment(
        self,
        sentiment: SentimentLevel,
        only_active: bool = True
    ) -> List[ChatConversation]:
        """Get conversations by sentiment level"""
        query = self.db.query(ChatConversation).filter(
            ChatConversation.current_sentiment == sentiment,
            ChatConversation.deleted_at.is_(None)
        )

        if only_active:
            query = query.filter(ChatConversation.is_active == True)

        return query.order_by(
            desc(ChatConversation.last_activity_at)
        ).all()

    def get_conversations_by_channel(
        self,
        channel: ConversationChannel,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ChatConversation]:
        """Get conversations by channel and date range"""
        query = self.db.query(ChatConversation).filter(
            ChatConversation.channel == channel,
            ChatConversation.deleted_at.is_(None)
        )

        if start_date:
            query = query.filter(ChatConversation.started_at >= start_date)
        if end_date:
            query = query.filter(ChatConversation.started_at <= end_date)

        return query.order_by(
            desc(ChatConversation.started_at)
        ).all()

    def update(self, conversation_id: int, updates: Dict) -> Optional[ChatConversation]:
        """Update chat conversation"""
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None

        for key, value in updates.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)

        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def mark_resolved(
        self,
        conversation_id: int,
        resolution_notes: Optional[str] = None
    ) -> Optional[ChatConversation]:
        """Mark conversation as resolved"""
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None

        conversation.is_resolved = True
        conversation.is_active = False
        conversation.resolution_notes = resolution_notes
        conversation.ended_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def soft_delete(self, conversation_id: int) -> bool:
        """Soft delete chat conversation"""
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return False

        conversation.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        channel: Optional[ConversationChannel] = None
    ) -> Dict:
        """Get chat conversation statistics"""
        query = self.db.query(ChatConversation).filter(
            ChatConversation.deleted_at.is_(None)
        )

        if start_date:
            query = query.filter(ChatConversation.started_at >= start_date)
        if end_date:
            query = query.filter(ChatConversation.started_at <= end_date)
        if channel:
            query = query.filter(ChatConversation.channel == channel)

        total_conversations = query.count()

        # Calculate averages
        avg_messages = self.db.query(
            func.avg(ChatConversation.total_messages)
        ).filter(
            ChatConversation.deleted_at.is_(None)
        ).scalar() or 0

        avg_quality = self.db.query(
            func.avg(ChatConversation.quality_score)
        ).filter(
            ChatConversation.deleted_at.is_(None),
            ChatConversation.quality_score.isnot(None)
        ).scalar() or 0

        # Conversion rates
        converted_to_lead = query.filter(
            ChatConversation.converted_to_lead == True
        ).count()

        converted_to_appointment = query.filter(
            ChatConversation.converted_to_appointment == True
        ).count()

        # Resolution rate
        resolved_count = query.filter(
            ChatConversation.is_resolved == True
        ).count()

        # Escalation rate
        escalated_count = query.filter(
            ChatConversation.escalated == True
        ).count()

        return {
            "total_conversations": total_conversations,
            "average_messages": float(avg_messages),
            "average_quality_score": float(avg_quality),
            "conversion_to_lead_rate": (converted_to_lead / total_conversations * 100) if total_conversations > 0 else 0,
            "conversion_to_appointment_rate": (converted_to_appointment / total_conversations * 100) if total_conversations > 0 else 0,
            "resolution_rate": (resolved_count / total_conversations * 100) if total_conversations > 0 else 0,
            "escalation_rate": (escalated_count / total_conversations * 100) if total_conversations > 0 else 0,
            "converted_to_lead_count": converted_to_lead,
            "converted_to_appointment_count": converted_to_appointment
        }


class ConversationMessageRepository:
    """Repository for conversation message data access"""

    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def create(self, message_data: Dict) -> ConversationMessage:
        """Create new conversation message"""
        message = ConversationMessage(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # Update conversation message counts and last activity
        self._update_conversation_metrics(message.conversation_id)

        return message

    def _update_conversation_metrics(self, conversation_id: int):
        """Update conversation message counts and timestamp"""
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if conversation:
            conversation.total_messages += 1
            conversation.last_activity_at = datetime.utcnow()
            self.db.commit()

    def get_by_conversation(
        self,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """Get messages for a conversation"""
        query = self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(
            ConversationMessage.sequence_number.asc()
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_recent_messages(
        self,
        conversation_id: int,
        count: int = 20
    ) -> List[ConversationMessage]:
        """Get most recent messages for a conversation"""
        return self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(
            desc(ConversationMessage.sequence_number)
        ).limit(count).all()

    def get_user_messages(
        self,
        conversation_id: int
    ) -> List[ConversationMessage]:
        """Get only user messages from conversation"""
        return self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.role == MessageRole.USER
        ).order_by(
            ConversationMessage.sequence_number.asc()
        ).all()

    def get_messages_with_buying_signals(
        self,
        conversation_id: int
    ) -> List[ConversationMessage]:
        """Get messages containing buying signals"""
        return self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.contains_buying_signal == True
        ).order_by(
            ConversationMessage.sequence_number.asc()
        ).all()


class SentimentAnalysisRepository:
    """Repository for sentiment analysis data access"""

    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def create(self, analysis_data: Dict) -> SentimentAnalysis:
        """Create new sentiment analysis"""
        analysis = SentimentAnalysis(**analysis_data)
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_by_voice_interaction(
        self,
        voice_interaction_id: int
    ) -> List[SentimentAnalysis]:
        """Get sentiment analyses for a voice interaction"""
        return self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.voice_interaction_id == voice_interaction_id
        ).order_by(
            desc(SentimentAnalysis.analysis_timestamp)
        ).all()

    def get_by_chat_conversation(
        self,
        chat_conversation_id: int
    ) -> List[SentimentAnalysis]:
        """Get sentiment analyses for a chat conversation"""
        return self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.chat_conversation_id == chat_conversation_id
        ).order_by(
            desc(SentimentAnalysis.analysis_timestamp)
        ).all()

    def get_alerts(
        self,
        severity: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[SentimentAnalysis]:
        """Get triggered sentiment alerts"""
        query = self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.alert_triggered == True
        )

        if severity:
            query = query.filter(SentimentAnalysis.alert_severity == severity)
        if since:
            query = query.filter(SentimentAnalysis.analysis_timestamp >= since)

        return query.order_by(
            desc(SentimentAnalysis.analysis_timestamp)
        ).all()

    def get_negative_sentiments(
        self,
        since: Optional[datetime] = None,
        min_urgency: float = 5.0
    ) -> List[SentimentAnalysis]:
        """Get negative sentiments with high urgency"""
        query = self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.sentiment_level.in_([
                SentimentLevel.NEGATIVE,
                SentimentLevel.VERY_NEGATIVE
            ]),
            SentimentAnalysis.urgency_score >= min_urgency
        )

        if since:
            query = query.filter(SentimentAnalysis.analysis_timestamp >= since)

        return query.order_by(
            desc(SentimentAnalysis.urgency_score)
        ).all()


class ConversationQualityRepository:
    """Repository for conversation quality data access"""

    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def create(self, quality_data: Dict) -> ConversationQuality:
        """Create new conversation quality analysis"""
        quality = ConversationQuality(**quality_data)
        self.db.add(quality)
        self.db.commit()
        self.db.refresh(quality)
        return quality

    def get_by_voice_interaction(
        self,
        voice_interaction_id: int
    ) -> Optional[ConversationQuality]:
        """Get quality analysis for a voice interaction"""
        return self.db.query(ConversationQuality).filter(
            ConversationQuality.voice_interaction_id == voice_interaction_id
        ).order_by(
            desc(ConversationQuality.analysis_timestamp)
        ).first()

    def get_by_chat_conversation(
        self,
        chat_conversation_id: int
    ) -> Optional[ConversationQuality]:
        """Get quality analysis for a chat conversation"""
        return self.db.query(ConversationQuality).filter(
            ConversationQuality.chat_conversation_id == chat_conversation_id
        ).order_by(
            desc(ConversationQuality.analysis_timestamp)
        ).first()

    def get_low_quality_conversations(
        self,
        max_score: float = 60.0,
        since: Optional[datetime] = None
    ) -> List[ConversationQuality]:
        """Get low quality conversations needing attention"""
        query = self.db.query(ConversationQuality).filter(
            ConversationQuality.overall_score <= max_score
        )

        if since:
            query = query.filter(ConversationQuality.analysis_timestamp >= since)

        return query.order_by(
            ConversationQuality.overall_score.asc()
        ).all()

    def get_conversations_needing_training(self) -> List[ConversationQuality]:
        """Get conversations where training is recommended"""
        return self.db.query(ConversationQuality).filter(
            ConversationQuality.training_needed == True
        ).order_by(
            desc(ConversationQuality.analysis_timestamp)
        ).all()

    def get_average_quality_by_agent(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Tuple[int, float]]:
        """Get average quality scores by agent"""
        # This would join with voice_interactions or chat_conversations
        # to get agent assignments and calculate averages
        # Implementation depends on your specific data model
        query = self.db.query(
            VoiceInteraction.assigned_agent_id,
            func.avg(ConversationQuality.overall_score).label('avg_score')
        ).join(
            ConversationQuality,
            ConversationQuality.voice_interaction_id == VoiceInteraction.id
        ).filter(
            VoiceInteraction.assigned_agent_id.isnot(None)
        )

        if start_date:
            query = query.filter(ConversationQuality.analysis_timestamp >= start_date)
        if end_date:
            query = query.filter(ConversationQuality.analysis_timestamp <= end_date)

        return query.group_by(
            VoiceInteraction.assigned_agent_id
        ).all()
