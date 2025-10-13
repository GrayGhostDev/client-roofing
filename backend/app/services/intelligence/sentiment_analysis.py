"""
Sentiment Analysis Service using OpenAI GPT-5
Real-time sentiment detection for all customer communications

Features:
- Multi-level sentiment analysis (positive/neutral/negative)
- Emotion detection (joy, anger, frustration, excitement)
- Urgency scoring (0-10 scale)
- Buying signal detection
- Alert triggering for negative sentiment
- Database persistence for all analyses
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.models.conversation_sqlalchemy import (
    SentimentAnalysis as SentimentAnalysisModel,
    SentimentLevel as SentimentLevelEnum,
    UrgencyLevel as UrgencyLevelEnum,
)
from app.repositories.conversation_repository import SentimentAnalysisRepository
from app.database import get_db_session

logger = logging.getLogger(__name__)

# OpenAI GPT-5 Client
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


class SentimentLevel(str, Enum):
    """Sentiment classification levels"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class EmotionType(str, Enum):
    """Primary emotion types"""
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"
    FRUSTRATION = "frustration"
    EXCITEMENT = "excitement"


class SentimentAnalysisService:
    """
    Sentiment Analysis Service using GPT-5

    Provides:
    - Real-time sentiment scoring
    - Emotion detection and classification
    - Urgency level assessment
    - Buying signal identification
    - Alert generation for negative sentiment
    - Database persistence for all analyses
    """

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize sentiment analysis service

        Args:
            db: Optional database session for persistence
        """
        self.model = "gpt-5"
        self.alert_threshold = -0.6  # Trigger alert if sentiment < -0.6
        self.db = db
        self._owns_db_session = db is None

    async def analyze_text(
        self,
        text: str,
        context: Optional[Dict] = None,
        source: str = "conversation",
        voice_interaction_id: Optional[int] = None,
        chat_conversation_id: Optional[int] = None,
        message_id: Optional[int] = None
    ) -> Dict:
        """
        Comprehensive sentiment analysis using GPT-5 with database persistence

        Args:
            text: Text to analyze (message, transcript, email)
            context: Additional context for analysis
            source: Source type (conversation, email, sms, call)
            voice_interaction_id: Link to voice interaction
            chat_conversation_id: Link to chat conversation
            message_id: Link to specific message

        Returns:
            Complete sentiment analysis with scores, alerts, and database ID
        """
        db_session = None
        try:
            # Get or create database session
            if self.db:
                db_session = self.db
            else:
                db_session = next(get_db_session())

            repo = SentimentAnalysisRepository(db_session)

            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(text, context, source)

            # Call GPT-5 with high reasoning for accurate sentiment detection
            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": analysis_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this {source}:\\n\\n{text}"
                    }
                ],
                temperature=0.2,  # Low temperature for consistent analysis
                reasoning_effort="high",  # GPT-5: Deep reasoning for accuracy
                response_format={"type": "json_object"}
            )

            # Parse GPT-5 response
            result = json.loads(response.choices[0].message.content)

            # Map sentiment string to enum
            sentiment_mapping = {
                "very_positive": SentimentLevelEnum.VERY_POSITIVE,
                "positive": SentimentLevelEnum.POSITIVE,
                "neutral": SentimentLevelEnum.NEUTRAL,
                "negative": SentimentLevelEnum.NEGATIVE,
                "very_negative": SentimentLevelEnum.VERY_NEGATIVE
            }
            sentiment_enum = sentiment_mapping.get(
                result.get("sentiment", "neutral"),
                SentimentLevelEnum.NEUTRAL
            )

            # Calculate urgency score and level
            urgency_score = float(result.get("urgency_score", 5.0))
            urgency_level = self._score_to_urgency_level(urgency_score)

            # Check if alert should be triggered
            sentiment_score = float(result.get("sentiment_score", 0.0))
            alert_triggered = sentiment_score < self.alert_threshold

            # Prepare database record
            sentiment_data = {
                "voice_interaction_id": voice_interaction_id,
                "chat_conversation_id": chat_conversation_id,
                "message_id": message_id,
                "sentiment_level": sentiment_enum,
                "sentiment_score": sentiment_score,
                "confidence": float(result.get("confidence", 0.8)),
                "emotions": result.get("emotions", {}),
                "dominant_emotion": result.get("dominant_emotion", "neutral"),
                "urgency_score": urgency_score,
                "urgency_level": urgency_level,
                "buying_signals": result.get("buying_signals", []),
                "pain_points": result.get("pain_points", []),
                "objections": result.get("objections", []),
                "key_phrases": result.get("key_phrases", []),
                "requires_attention": result.get("requires_attention", False),
                "recommended_action": result.get("recommended_action", "Continue conversation"),
                "alert_triggered": alert_triggered,
                "alert_reason": f"Negative sentiment detected: {sentiment_enum.value}" if alert_triggered else None,
                "analyzed_text_preview": text[:500] if len(text) > 500 else text,
                "source_type": source,
                "context_data": context or {}
            }

            # Save to database
            db_sentiment = repo.create(sentiment_data)

            if alert_triggered:
                logger.warning(f"Sentiment alert triggered for {source}: {text[:100]}")

            # Build response with database ID
            analysis = {
                "id": db_sentiment.id,  # Database ID
                "text": text,
                "source": source,
                "timestamp": db_sentiment.created_at.isoformat(),
                "sentiment": {
                    "level": sentiment_enum.value,
                    "score": sentiment_score,
                    "confidence": float(result.get("confidence", 0.8))
                },
                "emotions": result.get("emotions", {}),
                "dominant_emotion": result.get("dominant_emotion", "neutral"),
                "urgency": {
                    "score": urgency_score,
                    "level": urgency_level.value
                },
                "buying_signals": result.get("buying_signals", []),
                "pain_points": result.get("pain_points", []),
                "objections": result.get("objections", []),
                "key_phrases": result.get("key_phrases", []),
                "requires_attention": result.get("requires_attention", False),
                "recommended_action": result.get("recommended_action", "Continue conversation"),
                "alert_triggered": alert_triggered,
                "alert_reason": sentiment_data["alert_reason"]
            }

            return analysis

        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}", exc_info=True)
            return self._default_analysis(text, source)
        finally:
            # Close database session if we created it
            if self._owns_db_session and db_session:
                db_session.close()

    async def analyze_conversation_thread(
        self,
        messages: List[Dict],
        conversation_id: str
    ) -> Dict:
        """
        Analyze entire conversation thread for sentiment trends

        Args:
            messages: List of conversation messages
            conversation_id: Conversation identifier

        Returns:
            Thread-level sentiment analysis with trends
        """
        try:
            # Analyze each message
            message_analyses = []
            for msg in messages:
                if msg.get("role") == "user":  # Only analyze user messages
                    analysis = await self.analyze_text(
                        text=msg.get("content", ""),
                        context={"conversation_id": conversation_id},
                        source="conversation"
                    )
                    message_analyses.append(analysis)

            if not message_analyses:
                return {"error": "No user messages to analyze"}

            # Calculate thread-level metrics
            sentiment_scores = [a["sentiment"]["score"] for a in message_analyses]
            urgency_scores = [a["urgency"]["score"] for a in message_analyses]

            thread_analysis = {
                "conversation_id": conversation_id,
                "message_count": len(message_analyses),
                "overall_sentiment": {
                    "average_score": sum(sentiment_scores) / len(sentiment_scores),
                    "trend": self._calculate_trend(sentiment_scores),
                    "min_score": min(sentiment_scores),
                    "max_score": max(sentiment_scores)
                },
                "overall_urgency": {
                    "average_score": sum(urgency_scores) / len(urgency_scores),
                    "max_urgency": max(urgency_scores)
                },
                "all_buying_signals": self._aggregate_list_field(message_analyses, "buying_signals"),
                "all_pain_points": self._aggregate_list_field(message_analyses, "pain_points"),
                "all_objections": self._aggregate_list_field(message_analyses, "objections"),
                "sentiment_deteriorating": self._is_deteriorating(sentiment_scores),
                "requires_immediate_attention": any(a["alert_triggered"] for a in message_analyses),
                "message_analyses": message_analyses,
                "timestamp": datetime.utcnow().isoformat()
            }

            return thread_analysis

        except Exception as e:
            logger.error(f"Thread analysis error: {str(e)}")
            return {"error": str(e)}

    async def detect_buying_signals(self, text: str) -> List[str]:
        """
        Detect buying signals in customer communication using GPT-5

        Args:
            text: Customer message

        Returns:
            List of detected buying signals
        """
        try:
            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Identify buying signals in roofing customer messages. Buying signals include:
- Budget/pricing questions
- Timeline inquiries ("how soon", "when can you")
- Decision-making language ("we decided", "ready to move forward")
- Comparison shopping ("vs competitors")
- Specific product interest
- Urgency indicators
- Request for proposals/quotes

Return JSON: {\"signals\": [\"signal1\", \"signal2\"], \"confidence\": 0-1}"""
                    },
                    {
                        "role": "user",
                        "content": f"Detect buying signals in:\\n{text}"
                    }
                ],
                temperature=0.3,
                reasoning_effort="medium",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("signals", [])

        except Exception as e:
            logger.error(f"Buying signal detection error: {str(e)}")
            return []

    async def assess_customer_satisfaction(
        self,
        interaction_text: str,
        interaction_type: str = "conversation"
    ) -> Dict:
        """
        Assess customer satisfaction level from interaction using GPT-5

        Args:
            interaction_text: Full interaction text
            interaction_type: Type of interaction

        Returns:
            Satisfaction assessment with CSAT score
        """
        try:
            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Assess customer satisfaction from interactions. Provide:
1. CSAT score (1-5): 5=very satisfied, 4=satisfied, 3=neutral, 2=dissatisfied, 1=very dissatisfied
2. Satisfaction indicators (what suggests this score)
3. Improvement opportunities
4. Likelihood to recommend (0-10, NPS style)

Return JSON format."""
                    },
                    {
                        "role": "user",
                        "content": f"Assess satisfaction from this {interaction_type}:\\n\\n{interaction_text}"
                    }
                ],
                temperature=0.3,
                verbosity="medium",
                reasoning_effort="high",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "csat_score": float(result.get("csat_score", 3.0)),
                "nps_score": float(result.get("nps_score", 5.0)),
                "satisfaction_level": result.get("satisfaction_level", "neutral"),
                "positive_indicators": result.get("positive_indicators", []),
                "negative_indicators": result.get("negative_indicators", []),
                "improvement_opportunities": result.get("improvement_opportunities", []),
                "confidence": float(result.get("confidence", 0.7)),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Satisfaction assessment error: {str(e)}")
            return {
                "csat_score": 3.0,
                "error": str(e)
            }

    def _build_analysis_prompt(self, text: str, context: Optional[Dict], source: str) -> str:
        """Build comprehensive analysis prompt for GPT-5"""
        return f"""You are an expert sentiment analyst for a roofing company. Analyze customer communications comprehensively.

Source: {source}
Context: {json.dumps(context or {})}

Provide detailed JSON analysis:
{{
  "sentiment": "very_positive|positive|neutral|negative|very_negative",
  "sentiment_score": -1.0 to 1.0 (numeric scale),
  "confidence": 0.0 to 1.0 (how confident in assessment),
  "emotions": {{"joy": 0-1, "anger": 0-1, "frustration": 0-1, "excitement": 0-1, "fear": 0-1}},
  "dominant_emotion": "primary emotion",
  "urgency_score": 0 to 10 (how urgent is customer need),
  "buying_signals": ["list", "of", "buying", "signals"],
  "pain_points": ["customer", "pain", "points"],
  "objections": ["customer", "objections"],
  "key_phrases": ["important", "phrases"],
  "requires_attention": boolean (needs immediate human response),
  "recommended_action": "suggested next step"
}}

Consider:
- Tone and language intensity
- Explicit and implicit emotional indicators
- Urgency markers (words like "urgent", "asap", "emergency", "leak")
- Buying intent (budget, timeline, decision-making language)
- Satisfaction indicators (positive/negative feedback)
- Frustration signals (complaints, repetition, negative comparisons)"""

    def _categorize_urgency(self, score: float) -> str:
        """Categorize urgency score into levels"""
        if score >= 8:
            return "critical"
        elif score >= 6:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"

    def _score_to_urgency_level(self, score: float) -> UrgencyLevelEnum:
        """
        Convert urgency score to UrgencyLevel enum

        Args:
            score: Urgency score (0.0 to 10.0)

        Returns:
            UrgencyLevel enum value
        """
        if score >= 8.0:
            return UrgencyLevelEnum.CRITICAL
        elif score >= 6.0:
            return UrgencyLevelEnum.HIGH
        elif score >= 4.0:
            return UrgencyLevelEnum.MEDIUM
        else:
            return UrgencyLevelEnum.LOW

    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate sentiment trend from score sequence"""
        if len(scores) < 2:
            return "stable"

        # Compare first half vs second half
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

        diff = second_half_avg - first_half_avg

        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "deteriorating"
        else:
            return "stable"

    def _is_deteriorating(self, scores: List[float]) -> bool:
        """Check if sentiment is deteriorating"""
        if len(scores) < 3:
            return False

        # Check if last 3 scores show declining trend
        recent = scores[-3:]
        return recent[0] > recent[1] > recent[2] and recent[2] < 0

    def _aggregate_list_field(self, analyses: List[Dict], field: str) -> List[str]:
        """Aggregate list field from multiple analyses"""
        aggregated = []
        for analysis in analyses:
            aggregated.extend(analysis.get(field, []))
        return list(set(aggregated))  # Remove duplicates

    def _default_analysis(self, text: str, source: str) -> Dict:
        """Return default analysis on error"""
        return {
            "text": text,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment": {
                "level": "neutral",
                "score": 0.0,
                "confidence": 0.5
            },
            "emotions": {},
            "dominant_emotion": "neutral",
            "urgency": {
                "score": 5.0,
                "level": "medium"
            },
            "buying_signals": [],
            "pain_points": [],
            "objections": [],
            "key_phrases": [],
            "requires_attention": False,
            "recommended_action": "Review manually",
            "alert_triggered": False,
            "error": "Analysis failed, using default values"
        }


# Global instance (requires database session for full functionality)
# Usage: sentiment_analysis_service = SentimentAnalysisService(db=db_session)
sentiment_analysis_service = None  # Initialize with database session when needed
