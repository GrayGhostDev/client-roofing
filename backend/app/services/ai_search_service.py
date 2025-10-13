"""
AI-Powered Search Service
Uses OpenAI GPT-4o to understand natural language queries and retrieve relevant data
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.lead_sqlalchemy import Lead
from app.models.customer_sqlalchemy import Customer
from app.models.project_sqlalchemy import Project
from app.models.conversation_sqlalchemy import VoiceInteraction, ChatConversation
from app.models.appointment_sqlalchemy import Appointment
from app.services.call_transcription import get_openai_client

logger = logging.getLogger(__name__)


class AISearchService:
    """
    AI-powered search service that interprets natural language queries
    and retrieves relevant data from the database
    """

    def __init__(self, db: Session):
        self.db = db
        self.openai_client = get_openai_client()

    async def process_search_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a natural language search query using GPT-4o

        Args:
            query: Natural language search query from user
            context: Optional context about the search (filters, date ranges, etc.)

        Returns:
            Dictionary containing search results and metadata
        """
        try:
            # Step 1: Use GPT-4o to understand the query intent
            search_intent = await self._analyze_query_intent(query, context)

            # Step 2: Build database query based on intent
            results = await self._execute_search(search_intent)

            # Step 3: Format results for user
            formatted_results = self._format_search_results(results, search_intent)

            return {
                "success": True,
                "query": query,
                "intent": search_intent,
                "results": formatted_results,
                "result_count": len(formatted_results),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"AI search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _analyze_query_intent(self, query: str, context: Optional[Dict]) -> Dict[str, Any]:
        """
        Use GPT-4o to analyze the search query and determine intent
        """
        if not self.openai_client:
            # Fallback to basic keyword search
            return self._fallback_intent_analysis(query)

        system_prompt = """You are an AI assistant helping to interpret search queries for a roofing CRM system.

Available data types:
- Leads: Potential customers, contact info, lead status, source
- Customers: Converted leads, project history, tier
- Projects: Roofing projects, status, value, timeline
- Voice Calls: AI voice interactions, transcripts, sentiment
- Chatbot Conversations: Chat interactions, messages
- Appointments: Scheduled meetings, inspections

Analyze the user's query and return a JSON object with:
{
    "entity_type": "leads|customers|projects|voice_calls|chatbot|appointments",
    "search_fields": ["field1", "field2"],
    "filters": {
        "status": "value",
        "date_range": {"start": "date", "end": "date"},
        "numeric_range": {"field": "value", "operator": "gt|lt|eq"}
    },
    "sort_by": "field",
    "limit": 20,
    "intent_description": "Brief description of what user is looking for"
}"""

        user_prompt = f"Search query: '{query}'"
        if context:
            user_prompt += f"\n\nAdditional context: {context}"

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            intent = response.choices[0].message.content
            import json
            return json.loads(intent)

        except Exception as e:
            logger.error(f"GPT-4o intent analysis error: {str(e)}")
            return self._fallback_intent_analysis(query)

    def _fallback_intent_analysis(self, query: str) -> Dict[str, Any]:
        """
        Fallback intent analysis using keyword matching
        """
        query_lower = query.lower()

        # Determine entity type
        if any(word in query_lower for word in ['lead', 'prospect', 'potential customer']):
            entity_type = 'leads'
        elif any(word in query_lower for word in ['customer', 'client']):
            entity_type = 'customers'
        elif any(word in query_lower for word in ['project', 'roof', 'job']):
            entity_type = 'projects'
        elif any(word in query_lower for word in ['call', 'voice', 'phone']):
            entity_type = 'voice_calls'
        elif any(word in query_lower for word in ['chat', 'conversation', 'message']):
            entity_type = 'chatbot'
        elif any(word in query_lower for word in ['appointment', 'meeting', 'inspection']):
            entity_type = 'appointments'
        else:
            entity_type = 'leads'  # Default

        # Extract status filters
        filters = {}
        if 'new' in query_lower:
            filters['status'] = 'new'
        elif 'contacted' in query_lower:
            filters['status'] = 'contacted'
        elif 'qualified' in query_lower:
            filters['status'] = 'qualified'
        elif 'hot' in query_lower:
            filters['temperature'] = 'hot'

        # Extract time filters
        if 'today' in query_lower:
            filters['date_range'] = {
                'start': datetime.utcnow().date().isoformat(),
                'end': datetime.utcnow().date().isoformat()
            }
        elif 'week' in query_lower:
            filters['date_range'] = {
                'start': (datetime.utcnow() - timedelta(days=7)).isoformat(),
                'end': datetime.utcnow().isoformat()
            }
        elif 'month' in query_lower:
            filters['date_range'] = {
                'start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                'end': datetime.utcnow().isoformat()
            }

        return {
            "entity_type": entity_type,
            "search_fields": ["all"],
            "filters": filters,
            "sort_by": "created_at",
            "limit": 20,
            "intent_description": f"Search for {entity_type}"
        }

    async def _execute_search(self, intent: Dict[str, Any]) -> List[Any]:
        """
        Execute database search based on analyzed intent
        """
        entity_type = intent.get('entity_type', 'leads')
        filters = intent.get('filters', {})
        limit = intent.get('limit', 20)

        if entity_type == 'leads':
            return self._search_leads(filters, limit)
        elif entity_type == 'customers':
            return self._search_customers(filters, limit)
        elif entity_type == 'projects':
            return self._search_projects(filters, limit)
        elif entity_type == 'voice_calls':
            return self._search_voice_calls(filters, limit)
        elif entity_type == 'chatbot':
            return self._search_chatbot_conversations(filters, limit)
        elif entity_type == 'appointments':
            return self._search_appointments(filters, limit)
        else:
            return []

    def _search_leads(self, filters: Dict, limit: int) -> List[Lead]:
        """Search leads with filters"""
        query = self.db.query(Lead).filter(Lead.is_deleted == False)

        if 'status' in filters:
            query = query.filter(Lead.status == filters['status'])

        if 'temperature' in filters:
            query = query.filter(Lead.temperature == filters['temperature'])

        if 'date_range' in filters:
            start = filters['date_range'].get('start')
            end = filters['date_range'].get('end')
            if start:
                query = query.filter(Lead.created_at >= start)
            if end:
                query = query.filter(Lead.created_at <= end)

        return query.order_by(Lead.created_at.desc()).limit(limit).all()

    def _search_customers(self, filters: Dict, limit: int) -> List[Customer]:
        """Search customers with filters"""
        query = self.db.query(Customer).filter(Customer.is_deleted == False)

        if 'tier' in filters:
            query = query.filter(Customer.tier == filters['tier'])

        if 'date_range' in filters:
            start = filters['date_range'].get('start')
            end = filters['date_range'].get('end')
            if start:
                query = query.filter(Customer.created_at >= start)
            if end:
                query = query.filter(Customer.created_at <= end)

        return query.order_by(Customer.created_at.desc()).limit(limit).all()

    def _search_projects(self, filters: Dict, limit: int) -> List[Project]:
        """Search projects with filters"""
        query = self.db.query(Project).filter(Project.is_deleted == False)

        if 'status' in filters:
            query = query.filter(Project.status == filters['status'])

        if 'date_range' in filters:
            start = filters['date_range'].get('start')
            end = filters['date_range'].get('end')
            if start:
                query = query.filter(Project.created_at >= start)
            if end:
                query = query.filter(Project.created_at <= end)

        return query.order_by(Project.created_at.desc()).limit(limit).all()

    def _search_voice_calls(self, filters: Dict, limit: int) -> List[VoiceInteraction]:
        """Search voice interactions with filters"""
        query = self.db.query(VoiceInteraction)

        if 'sentiment' in filters:
            query = query.filter(VoiceInteraction.sentiment == filters['sentiment'])

        if 'date_range' in filters:
            start = filters['date_range'].get('start')
            end = filters['date_range'].get('end')
            if start:
                query = query.filter(VoiceInteraction.call_started_at >= start)
            if end:
                query = query.filter(VoiceInteraction.call_started_at <= end)

        return query.order_by(VoiceInteraction.call_started_at.desc()).limit(limit).all()

    def _search_chatbot_conversations(self, filters: Dict, limit: int) -> List[ChatConversation]:
        """Search chatbot conversations with filters"""
        query = self.db.query(ChatConversation)

        if 'status' in filters:
            query = query.filter(ChatConversation.status == filters['status'])

        if 'date_range' in filters:
            start = filters['date_range'].get('start')
            end = filters['date_range'].get('end')
            if start:
                query = query.filter(ChatConversation.started_at >= start)
            if end:
                query = query.filter(ChatConversation.started_at <= end)

        return query.order_by(ChatConversation.started_at.desc()).limit(limit).all()

    def _search_appointments(self, filters: Dict, limit: int) -> List[Appointment]:
        """Search appointments with filters"""
        query = self.db.query(Appointment).filter(Appointment.is_deleted == False)

        if 'status' in filters:
            query = query.filter(Appointment.status == filters['status'])

        if 'date_range' in filters:
            start = filters['date_range'].get('start')
            end = filters['date_range'].get('end')
            if start:
                query = query.filter(Appointment.scheduled_at >= start)
            if end:
                query = query.filter(Appointment.scheduled_at <= end)

        return query.order_by(Appointment.scheduled_at.desc()).limit(limit).all()

    def _format_search_results(self, results: List[Any], intent: Dict) -> List[Dict]:
        """
        Format search results for display
        """
        entity_type = intent.get('entity_type', 'unknown')
        formatted = []

        for result in results:
            if entity_type == 'leads':
                formatted.append(self._format_lead(result))
            elif entity_type == 'customers':
                formatted.append(self._format_customer(result))
            elif entity_type == 'projects':
                formatted.append(self._format_project(result))
            elif entity_type == 'voice_calls':
                formatted.append(self._format_voice_call(result))
            elif entity_type == 'chatbot':
                formatted.append(self._format_chatbot_conversation(result))
            elif entity_type == 'appointments':
                formatted.append(self._format_appointment(result))

        return formatted

    def _format_lead(self, lead: Lead) -> Dict:
        """Format lead for display"""
        return {
            "id": lead.id,
            "type": "lead",
            "name": f"{lead.first_name} {lead.last_name}",
            "status": lead.status.value if hasattr(lead.status, 'value') else lead.status,
            "temperature": lead.temperature.value if hasattr(lead.temperature, 'value') else lead.temperature,
            "phone": lead.phone,
            "email": lead.email,
            "source": lead.source.value if hasattr(lead.source, 'value') else lead.source,
            "lead_score": lead.lead_score,
            "created_at": lead.created_at.isoformat() if lead.created_at else None
        }

    def _format_customer(self, customer: Customer) -> Dict:
        """Format customer for display"""
        return {
            "id": customer.id,
            "type": "customer",
            "name": f"{customer.first_name} {customer.last_name}",
            "tier": customer.tier.value if hasattr(customer.tier, 'value') else customer.tier,
            "phone": customer.phone,
            "email": customer.email,
            "lifetime_value": customer.lifetime_value,
            "created_at": customer.created_at.isoformat() if customer.created_at else None
        }

    def _format_project(self, project: Project) -> Dict:
        """Format project for display"""
        return {
            "id": project.id,
            "type": "project",
            "title": project.title,
            "status": project.status.value if hasattr(project.status, 'value') else project.status,
            "project_value": project.project_value,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "created_at": project.created_at.isoformat() if project.created_at else None
        }

    def _format_voice_call(self, call: VoiceInteraction) -> Dict:
        """Format voice interaction for display"""
        return {
            "id": call.id,
            "type": "voice_call",
            "caller_name": call.caller_name,
            "phone_number": call.phone_number,
            "duration_seconds": call.call_duration_seconds,
            "intent": call.intent.value if call.intent else None,
            "sentiment": call.sentiment.value if call.sentiment else None,
            "summary": call.summary,
            "call_started_at": call.call_started_at.isoformat() if call.call_started_at else None
        }

    def _format_chatbot_conversation(self, conversation: ChatConversation) -> Dict:
        """Format chatbot conversation for display"""
        return {
            "id": conversation.id,
            "type": "chatbot_conversation",
            "status": conversation.status.value if hasattr(conversation.status, 'value') else conversation.status,
            "message_count": conversation.message_count,
            "sentiment": conversation.sentiment.value if conversation.sentiment else None,
            "started_at": conversation.started_at.isoformat() if conversation.started_at else None
        }

    def _format_appointment(self, appointment: Appointment) -> Dict:
        """Format appointment for display"""
        return {
            "id": appointment.id,
            "type": "appointment",
            "title": appointment.title,
            "status": appointment.status.value if hasattr(appointment.status, 'value') else appointment.status,
            "appointment_type": appointment.appointment_type.value if hasattr(appointment.appointment_type, 'value') else appointment.appointment_type,
            "scheduled_at": appointment.scheduled_at.isoformat() if appointment.scheduled_at else None,
            "created_at": appointment.created_at.isoformat() if appointment.created_at else None
        }
