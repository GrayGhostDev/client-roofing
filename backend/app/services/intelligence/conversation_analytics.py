"""
Conversation Analytics Engine for iSwitch Roofs CRM
Powered by OpenAI GPT-5 for comprehensive conversation intelligence

Features:
- Conversation quality scoring
- Intent classification and tracking
- Topic extraction and categorization
- Conversation flow analysis
- Response time analytics
- Conversion path tracking
- Performance metrics and KPIs
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from openai import AsyncOpenAI
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# OpenAI GPT-5 Client
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


class ConversationAnalyticsService:
    """
    Conversation Analytics Engine using GPT-5

    Provides:
    - Conversation quality scoring (0-100)
    - Intent classification and distribution
    - Topic extraction and trending
    - Conversation flow optimization insights
    - Performance metrics (response time, resolution rate)
    - Conversion path analysis
    - Agent performance analytics
    - Customer satisfaction trends
    """

    def __init__(self):
        """Initialize conversation analytics service"""
        self.model = "gpt-5"
        self.quality_thresholds = {
            "excellent": 90,
            "good": 75,
            "acceptable": 60,
            "needs_improvement": 40,
            "poor": 0
        }

    async def analyze_conversation_quality(
        self,
        conversation_id: str,
        messages: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Comprehensive conversation quality analysis using GPT-5

        Args:
            conversation_id: Unique conversation identifier
            messages: List of conversation messages
            metadata: Additional context (channel, agent, customer info)

        Returns:
            Detailed quality analysis with scores and recommendations
        """
        try:
            # Prepare conversation text
            conversation_text = self._format_conversation(messages)

            # Build comprehensive analysis prompt
            analysis_prompt = self._build_quality_analysis_prompt()

            # Call GPT-5 with high reasoning for detailed analysis
            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": f"Analyze this roofing customer conversation (ID: {conversation_id}):\\n\\n{conversation_text}\\n\\nMetadata: {json.dumps(metadata or {})}"}
                ],
                temperature=0.3,
                verbosity="high",  # GPT-5: Detailed analysis
                reasoning_effort="high",  # GPT-5: Deep reasoning
                response_format={"type": "json_object"}
            )

            # Parse GPT-5 analysis
            result = json.loads(response.choices[0].message.content)

            # Calculate composite quality score
            quality_score = self._calculate_quality_score(result)

            # Build comprehensive quality analysis
            quality_analysis = {
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_quality": {
                    "score": quality_score,
                    "grade": self._score_to_grade(quality_score),
                    "confidence": float(result.get("confidence", 0.8))
                },
                "dimensions": {
                    "professionalism": {
                        "score": float(result.get("professionalism_score", 75.0)),
                        "notes": result.get("professionalism_notes", "")
                    },
                    "responsiveness": {
                        "score": float(result.get("responsiveness_score", 75.0)),
                        "notes": result.get("responsiveness_notes", "")
                    },
                    "clarity": {
                        "score": float(result.get("clarity_score", 75.0)),
                        "notes": result.get("clarity_notes", "")
                    },
                    "helpfulness": {
                        "score": float(result.get("helpfulness_score", 75.0)),
                        "notes": result.get("helpfulness_notes", "")
                    },
                    "resolution": {
                        "score": float(result.get("resolution_score", 75.0)),
                        "notes": result.get("resolution_notes", ""),
                        "resolved": result.get("issue_resolved", False)
                    }
                },
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
                "improvement_opportunities": result.get("improvement_opportunities", []),
                "best_practices_followed": result.get("best_practices_followed", []),
                "missed_opportunities": result.get("missed_opportunities", []),
                "intent_handled": result.get("intent_handled", True),
                "escalation_appropriate": result.get("escalation_appropriate", None),
                "customer_satisfaction_estimate": float(result.get("csat_estimate", 3.5)),
                "conversion_likelihood": float(result.get("conversion_likelihood", 0.5)),
                "recommended_actions": result.get("recommended_actions", []),
                "message_count": len(messages),
                "metadata": metadata
            }

            return quality_analysis

        except Exception as e:
            logger.error(f"Conversation quality analysis error: {str(e)}")
            return self._default_quality_analysis(conversation_id, len(messages))

    async def extract_topics_and_intents(
        self,
        conversations: List[Dict],
        timeframe_days: int = 30
    ) -> Dict:
        """
        Extract and categorize topics and intents across multiple conversations using GPT-5

        Args:
            conversations: List of conversation dictionaries
            timeframe_days: Analysis timeframe

        Returns:
            Topic and intent distribution with trending analysis
        """
        try:
            # Aggregate all conversation summaries
            conversation_summaries = []
            for conv in conversations[:100]:  # Limit to 100 for performance
                summary = await self._summarize_conversation_gpt5(
                    conv.get("messages", []),
                    conv.get("conversation_id", "unknown")
                )
                conversation_summaries.append({
                    "id": conv.get("conversation_id"),
                    "summary": summary,
                    "date": conv.get("created_at", datetime.utcnow().isoformat())
                })

            # Use GPT-5 to extract topics and trends
            analysis_text = "\\n\\n".join([
                f"[{s['date']}] {s['summary']}" for s in conversation_summaries
            ])

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze roofing company conversations to identify:
1. Common topics (e.g., insurance claims, storm damage, pricing, scheduling)
2. Customer intents (quote request, emergency repair, routine maintenance)
3. Trending topics (what's increasing in frequency)
4. Seasonal patterns
5. Pain points mentioned repeatedly
6. Service gaps or unmet needs

Return JSON with:
{
  "top_topics": [{\"topic\": \"name\", \"count\": N, \"percentage\": X, \"trend\": \"rising|stable|falling\"}],
  "top_intents": [{\"intent\": \"name\", \"count\": N, \"percentage\": X}],
  "trending_topics": [\"topic1\", \"topic2\"],
  "seasonal_patterns": {\"topic\": \"pattern description\"},
  "common_pain_points": [\"pain1\", \"pain2\"],
  "service_gaps\": [\"gap1\", \"gap2\"],
  "insights\": [\"insight1\", \"insight2\"]
}"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze {len(conversation_summaries)} conversations from last {timeframe_days} days:\\n\\n{analysis_text[:8000]}"
                    }
                ],
                temperature=0.4,
                verbosity="high",
                reasoning_effort="high",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "timeframe_days": timeframe_days,
                "conversations_analyzed": len(conversations),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "topics": result.get("top_topics", []),
                "intents": result.get("top_intents", []),
                "trending": result.get("trending_topics", []),
                "seasonal_patterns": result.get("seasonal_patterns", {}),
                "pain_points": result.get("common_pain_points", []),
                "service_gaps": result.get("service_gaps", []),
                "insights": result.get("insights", [])
            }

        except Exception as e:
            logger.error(f"Topic extraction error: {str(e)}")
            return {"error": str(e)}

    async def analyze_conversion_path(
        self,
        conversation_id: str,
        messages: List[Dict],
        outcome: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze conversation flow and conversion path using GPT-5

        Args:
            conversation_id: Conversation identifier
            messages: Conversation messages
            outcome: Final outcome (converted, lost, pending)
            metadata: Additional context

        Returns:
            Conversion path analysis with key moments
        """
        try:
            conversation_text = self._format_conversation(messages)

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze roofing sales conversation for conversion path. Identify:
1. Key moments (turning points, objections overcome, buying signals)
2. Conversation stages (awareness, interest, consideration, decision)
3. Successful tactics used
4. Missed opportunities
5. Time to conversion indicators
6. Factors influencing outcome

Return JSON with detailed conversion path analysis."""
                    },
                    {
                        "role": "user",
                        "content": f"Conversation outcome: {outcome}\\n\\nConversation:\\n{conversation_text}\\n\\nMetadata: {json.dumps(metadata or {})}"
                    }
                ],
                temperature=0.3,
                verbosity="high",
                reasoning_effort="high",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "conversation_id": conversation_id,
                "outcome": outcome,
                "timestamp": datetime.utcnow().isoformat(),
                "conversion_stages": result.get("stages", []),
                "key_moments": result.get("key_moments", []),
                "turning_points": result.get("turning_points", []),
                "buying_signals_detected": result.get("buying_signals", []),
                "objections_raised": result.get("objections", []),
                "objections_overcome": result.get("objections_overcome", []),
                "successful_tactics": result.get("successful_tactics", []),
                "missed_opportunities": result.get("missed_opportunities", []),
                "time_to_decision": result.get("time_to_decision", "unknown"),
                "conversion_probability": float(result.get("conversion_probability", 0.5)),
                "influence_factors": result.get("influence_factors", {}),
                "recommendations": result.get("recommendations", []),
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Conversion path analysis error: {str(e)}")
            return {"error": str(e)}

    async def analyze_agent_performance(
        self,
        agent_id: str,
        conversations: List[Dict],
        timeframe_days: int = 30
    ) -> Dict:
        """
        Analyze individual agent performance using GPT-5

        Args:
            agent_id: Agent identifier
            conversations: Agent's conversations
            timeframe_days: Analysis period

        Returns:
            Comprehensive agent performance analysis
        """
        try:
            # Calculate basic metrics
            total_conversations = len(conversations)
            resolved_count = sum(1 for c in conversations if c.get("resolved", False))
            avg_messages = sum(len(c.get("messages", [])) for c in conversations) / max(total_conversations, 1)

            # Analyze sample conversations for qualitative assessment
            sample_conversations = conversations[:10]  # Analyze up to 10 conversations
            conversation_texts = []

            for conv in sample_conversations:
                text = self._format_conversation(conv.get("messages", []))
                conversation_texts.append(f"Conversation {conv.get('conversation_id')}:\\n{text}\\n---")

            analysis_text = "\\n\\n".join(conversation_texts)

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze agent performance in roofing sales conversations. Assess:
1. Communication quality (professionalism, clarity, tone)
2. Product knowledge (roofing expertise demonstrated)
3. Sales skills (questioning, objection handling, closing)
4. Customer service (empathy, responsiveness, problem-solving)
5. Efficiency (conciseness without sacrificing quality)
6. Strengths and areas for improvement
7. Training recommendations

Return JSON with detailed assessment."""
                    },
                    {
                        "role": "user",
                        "content": f"Agent {agent_id} - {total_conversations} conversations over {timeframe_days} days. Sample conversations:\\n\\n{analysis_text[:8000]}"
                    }
                ],
                temperature=0.3,
                verbosity="high",
                reasoning_effort="high",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "agent_id": agent_id,
                "timeframe_days": timeframe_days,
                "timestamp": datetime.utcnow().isoformat(),
                "quantitative_metrics": {
                    "total_conversations": total_conversations,
                    "resolved_count": resolved_count,
                    "resolution_rate": resolved_count / max(total_conversations, 1),
                    "average_messages_per_conversation": avg_messages,
                    "conversations_per_day": total_conversations / max(timeframe_days, 1)
                },
                "qualitative_assessment": {
                    "communication_quality": {
                        "score": float(result.get("communication_score", 75.0)),
                        "notes": result.get("communication_notes", "")
                    },
                    "product_knowledge": {
                        "score": float(result.get("product_knowledge_score", 75.0)),
                        "notes": result.get("product_knowledge_notes", "")
                    },
                    "sales_skills": {
                        "score": float(result.get("sales_skills_score", 75.0)),
                        "notes": result.get("sales_skills_notes", "")
                    },
                    "customer_service": {
                        "score": float(result.get("customer_service_score", 75.0)),
                        "notes": result.get("customer_service_notes", "")
                    },
                    "efficiency": {
                        "score": float(result.get("efficiency_score", 75.0)),
                        "notes": result.get("efficiency_notes", "")
                    }
                },
                "overall_performance_score": float(result.get("overall_score", 75.0)),
                "performance_grade": self._score_to_grade(float(result.get("overall_score", 75.0))),
                "strengths": result.get("strengths", []),
                "areas_for_improvement": result.get("areas_for_improvement", []),
                "training_recommendations": result.get("training_recommendations", []),
                "notable_achievements": result.get("notable_achievements", []),
                "consistency_rating": result.get("consistency_rating", "moderate")
            }

        except Exception as e:
            logger.error(f"Agent performance analysis error: {str(e)}")
            return {"error": str(e)}

    async def generate_conversation_insights(
        self,
        conversations: List[Dict],
        focus_area: Optional[str] = None
    ) -> Dict:
        """
        Generate actionable insights from conversation data using GPT-5

        Args:
            conversations: Conversation data
            focus_area: Optional specific focus (sales, support, quality)

        Returns:
            Actionable insights and recommendations
        """
        try:
            # Prepare aggregated data
            total_convs = len(conversations)
            avg_length = sum(len(c.get("messages", [])) for c in conversations) / max(total_convs, 1)

            # Sample conversations for deep analysis
            samples = conversations[:20]
            sample_summaries = []

            for conv in samples:
                summary = {
                    "id": conv.get("conversation_id"),
                    "outcome": conv.get("outcome", "unknown"),
                    "quality_score": conv.get("quality_score", 50),
                    "message_count": len(conv.get("messages", [])),
                    "resolved": conv.get("resolved", False)
                }
                sample_summaries.append(summary)

            focus_prompt = f" Focus specifically on {focus_area}." if focus_area else ""

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Analyze roofing company conversations to generate actionable business insights.{focus_prompt}

Provide:
1. Key findings (most important discoveries)
2. Patterns and trends (what's working, what's not)
3. Optimization opportunities (quick wins)
4. Strategic recommendations (long-term improvements)
5. Process improvements (workflow enhancements)
6. Training needs (skill gaps identified)
7. Technology recommendations (tools/features needed)

Return JSON with comprehensive insights."""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze {total_convs} conversations. Avg length: {avg_length:.1f} messages. Sample data:\\n{json.dumps(sample_summaries, indent=2)}"
                    }
                ],
                temperature=0.4,
                verbosity="high",
                reasoning_effort="high",
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "conversations_analyzed": total_convs,
                "focus_area": focus_area,
                "key_findings": result.get("key_findings", []),
                "patterns_and_trends": result.get("patterns_and_trends", []),
                "optimization_opportunities": result.get("optimization_opportunities", []),
                "strategic_recommendations": result.get("strategic_recommendations", []),
                "process_improvements": result.get("process_improvements", []),
                "training_needs": result.get("training_needs", []),
                "technology_recommendations": result.get("technology_recommendations", []),
                "estimated_impact": result.get("estimated_impact", {}),
                "implementation_priority": result.get("implementation_priority", [])
            }

        except Exception as e:
            logger.error(f"Insights generation error: {str(e)}")
            return {"error": str(e)}

    async def calculate_conversation_metrics(
        self,
        conversations: List[Dict],
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calculate comprehensive conversation metrics

        Args:
            conversations: List of conversations
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Complete metrics dashboard
        """
        try:
            total_conversations = len(conversations)

            if total_conversations == 0:
                return self._empty_metrics(start_date, end_date)

            # Calculate metrics
            resolved_conversations = [c for c in conversations if c.get("resolved", False)]
            avg_resolution_time = sum(
                (c.get("resolved_at", end_date) - c.get("created_at", start_date)).total_seconds() / 3600
                for c in resolved_conversations
            ) / max(len(resolved_conversations), 1)

            avg_messages = sum(len(c.get("messages", [])) for c in conversations) / total_conversations

            avg_response_time = sum(
                c.get("first_response_seconds", 0) for c in conversations
            ) / total_conversations

            # Intent distribution
            intent_counts = Counter(c.get("intent", "unknown") for c in conversations)

            # Sentiment distribution
            sentiment_counts = Counter(c.get("sentiment", "neutral") for c in conversations)

            # Quality scores
            quality_scores = [c.get("quality_score", 50) for c in conversations if "quality_score" in c]
            avg_quality = sum(quality_scores) / max(len(quality_scores), 1)

            # Satisfaction scores
            csat_scores = [c.get("csat_score", 3) for c in conversations if "csat_score" in c]
            avg_csat = sum(csat_scores) / max(len(csat_scores), 1)

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "volume_metrics": {
                    "total_conversations": total_conversations,
                    "conversations_per_day": total_conversations / max((end_date - start_date).days, 1),
                    "resolved_conversations": len(resolved_conversations),
                    "resolution_rate": len(resolved_conversations) / total_conversations,
                    "pending_conversations": total_conversations - len(resolved_conversations)
                },
                "efficiency_metrics": {
                    "average_messages_per_conversation": avg_messages,
                    "average_first_response_time_seconds": avg_response_time,
                    "average_resolution_time_hours": avg_resolution_time
                },
                "quality_metrics": {
                    "average_quality_score": avg_quality,
                    "quality_distribution": self._score_distribution(quality_scores),
                    "high_quality_conversations": sum(1 for s in quality_scores if s >= 80),
                    "low_quality_conversations": sum(1 for s in quality_scores if s < 60)
                },
                "satisfaction_metrics": {
                    "average_csat": avg_csat,
                    "csat_distribution": dict(Counter(csat_scores)),
                    "satisfied_customers": sum(1 for s in csat_scores if s >= 4),
                    "dissatisfied_customers": sum(1 for s in csat_scores if s <= 2)
                },
                "intent_distribution": dict(intent_counts),
                "sentiment_distribution": dict(sentiment_counts),
                "channel_distribution": dict(Counter(c.get("channel", "unknown") for c in conversations)),
                "peak_hours": self._calculate_peak_hours(conversations),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Metrics calculation error: {str(e)}")
            return {"error": str(e)}

    # Helper methods

    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation messages for GPT-5 analysis"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            formatted.append(f"[{role.upper()}] {content}")
        return "\\n\\n".join(formatted)

    async def _summarize_conversation_gpt5(self, messages: List[Dict], conv_id: str) -> str:
        """Summarize single conversation using GPT-5"""
        try:
            text = self._format_conversation(messages)

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Summarize roofing conversation in 2-3 sentences. Focus on customer need and outcome."},
                    {"role": "user", "content": text[:2000]}
                ],
                temperature=0.3,
                max_tokens=100,
                verbosity="low"
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Conversation summary error: {str(e)}")
            return f"Conversation {conv_id}"

    def _build_quality_analysis_prompt(self) -> str:
        """Build comprehensive quality analysis prompt"""
        return """You are a conversation quality analyst for a premium roofing company. Analyze conversations across multiple dimensions:

**Quality Dimensions (score each 0-100):**

1. **Professionalism** (0-100)
   - Tone and language appropriateness
   - Grammar and spelling
   - Brand representation
   - Courtesy and respect

2. **Responsiveness** (0-100)
   - Timeliness of responses
   - Addressing all customer questions
   - Proactive information sharing
   - Follow-through on commitments

3. **Clarity** (0-100)
   - Clear, concise communication
   - Avoiding jargon (unless appropriate)
   - Structured responses
   - Easy to understand

4. **Helpfulness** (0-100)
   - Providing useful information
   - Solving customer problems
   - Going above and beyond
   - Resourcefulness

5. **Resolution** (0-100)
   - Issue fully resolved
   - Customer needs met
   - Appropriate next steps
   - Closure achieved

**Provide JSON analysis:**
{
  "professionalism_score": 0-100,
  "professionalism_notes": "specific observations",
  "responsiveness_score": 0-100,
  "responsiveness_notes": "specific observations",
  "clarity_score": 0-100,
  "clarity_notes": "specific observations",
  "helpfulness_score": 0-100,
  "helpfulness_notes": "specific observations",
  "resolution_score": 0-100,
  "resolution_notes": "specific observations",
  "issue_resolved": boolean,
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "improvement_opportunities": ["opportunity1", "opportunity2"],
  "best_practices_followed": ["practice1", "practice2"],
  "missed_opportunities": ["missed1", "missed2"],
  "intent_handled": boolean,
  "escalation_appropriate": boolean or null,
  "csat_estimate": 1-5 estimated satisfaction,
  "conversion_likelihood": 0-1 probability,
  "recommended_actions": ["action1", "action2"],
  "confidence": 0-1 confidence in assessment
}"""

    def _calculate_quality_score(self, analysis: Dict) -> float:
        """Calculate composite quality score from dimensions"""
        scores = [
            float(analysis.get("professionalism_score", 75.0)),
            float(analysis.get("responsiveness_score", 75.0)),
            float(analysis.get("clarity_score", 75.0)),
            float(analysis.get("helpfulness_score", 75.0)),
            float(analysis.get("resolution_score", 75.0))
        ]
        return sum(scores) / len(scores)

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution"""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for score in scores:
            grade = self._score_to_grade(score)
            distribution[grade] += 1
        return distribution

    def _calculate_peak_hours(self, conversations: List[Dict]) -> Dict[int, int]:
        """Calculate peak conversation hours"""
        hour_counts = defaultdict(int)
        for conv in conversations:
            created_at = conv.get("created_at")
            if created_at:
                hour = created_at.hour if hasattr(created_at, 'hour') else 12
                hour_counts[hour] += 1
        return dict(sorted(hour_counts.items()))

    def _empty_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Return empty metrics structure"""
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "volume_metrics": {
                "total_conversations": 0,
                "conversations_per_day": 0,
                "resolved_conversations": 0,
                "resolution_rate": 0,
                "pending_conversations": 0
            },
            "message": "No conversations in this period"
        }

    def _default_quality_analysis(self, conversation_id: str, message_count: int) -> Dict:
        """Return default quality analysis on error"""
        return {
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_quality": {
                "score": 50.0,
                "grade": "C",
                "confidence": 0.5
            },
            "dimensions": {
                "professionalism": {"score": 50.0, "notes": "Unable to analyze"},
                "responsiveness": {"score": 50.0, "notes": "Unable to analyze"},
                "clarity": {"score": 50.0, "notes": "Unable to analyze"},
                "helpfulness": {"score": 50.0, "notes": "Unable to analyze"},
                "resolution": {"score": 50.0, "notes": "Unable to analyze", "resolved": False}
            },
            "message_count": message_count,
            "error": "Analysis failed, using default values"
        }


# Global instance
conversation_analytics_service = ConversationAnalyticsService()
