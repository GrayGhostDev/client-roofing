"""
CRM Assistant API Routes (Flask)
Intelligent chatbot that understands CRM context and helps with customer management
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
import os
import json

logger = logging.getLogger(__name__)
bp = Blueprint('crm_assistant', __name__)

# Try to import OpenAI, but gracefully handle if not available
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    OPENAI_AVAILABLE = True
except Exception as e:
    logger.warning(f"OpenAI not available: {e}")
    OPENAI_AVAILABLE = False

# Import database utilities
try:
    from app.database import get_db
    from app.models.lead_sqlalchemy import Lead
    from app.models.customer_sqlalchemy import Customer
    from app.models.project_sqlalchemy import Project
    from sqlalchemy import func
    DB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Database models not available: {e}")
    DB_AVAILABLE = False


def get_crm_context():
    """Get current CRM system context for AI assistant"""
    context = {
        "system_name": "iSwitch Roofs CRM",
        "capabilities": [
            "Lead management and tracking",
            "Customer relationship management",
            "Project tracking and analytics",
            "Appointment scheduling",
            "Sales automation and campaigns",
            "Real-time analytics and reporting"
        ],
        "current_data": {}
    }

    if not DB_AVAILABLE:
        return context

    try:
        # Use get_db() which returns a generator
        db = next(get_db())
        try:
            # Get real-time stats
            total_leads = db.query(func.count(Lead.id)).scalar() or 0
            hot_leads = db.query(func.count(Lead.id)).filter(Lead.lead_score >= 80).scalar() or 0
            total_customers = db.query(func.count(Customer.id)).scalar() or 0
            total_projects = db.query(func.count(Project.id)).scalar() or 0

            context["current_data"] = {
                "total_leads": total_leads,
                "hot_leads": hot_leads,
                "total_customers": total_customers,
                "total_projects": total_projects,
                "conversion_rate": round((total_customers / total_leads * 100) if total_leads > 0 else 0, 1)
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching CRM context: {e}")

    return context


def get_system_prompt():
    """Generate system prompt with current CRM context"""
    context = get_crm_context()

    return f"""You are an intelligent CRM assistant for {context['system_name']}, a roofing company's customer relationship management system.

CURRENT SYSTEM STATUS:
- Total Leads: {context['current_data'].get('total_leads', 0)}
- HOT Leads (Score ≥80): {context['current_data'].get('hot_leads', 0)}
- Total Customers: {context['current_data'].get('total_customers', 0)}
- Total Projects: {context['current_data'].get('total_projects', 0)}
- Conversion Rate: {context['current_data'].get('conversion_rate', 0)}%

YOUR CAPABILITIES:
1. **Lead Management**: Help users find, qualify, and convert leads
2. **Customer Tracking**: Assist with customer data, history, and lifecycle
3. **Project Updates**: Provide project status, timeline, and revenue information
4. **Data Entry**: Guide users through adding new leads, customers, or projects
5. **Analytics**: Explain metrics, trends, and business insights
6. **Navigation**: Help users find the right page or feature
7. **Workflow Guidance**: Suggest next steps for sales and customer success

YOUR PERSONALITY:
- Professional but friendly
- Proactive in suggesting actions
- Data-driven and specific
- Helpful with step-by-step guidance
- Use emojis sparingly for emphasis

IMPORTANT INSTRUCTIONS:
- Always reference real data from the system when available
- Provide specific, actionable recommendations
- If you don't have access to specific data, say so clearly
- Guide users to the appropriate page/tab for detailed actions
- Focus on helping users achieve their CRM goals efficiently

EXAMPLE INTERACTIONS:
User: "How many hot leads do we have?"
You: "You currently have {context['current_data'].get('hot_leads', 0)} HOT leads (score ≥80). These are your highest-priority prospects! 🔥 Would you like me to help you prioritize follow-ups or view details?"

User: "I need to add a new customer"
You: "I can guide you through adding a new customer! Here's what you'll need:
1. Contact information (name, email, phone)
2. Address details
3. Property information (optional but helpful)
4. Initial notes

Navigate to 'Customers Management' in the sidebar, then click the 'Add New Customer' button. Need help with any specific fields?"

User: "What's our conversion rate?"
You: "Your current conversion rate is {context['current_data'].get('conversion_rate', 0)}%. You have {context['current_data'].get('total_customers', 0)} customers from {context['current_data'].get('total_leads', 0)} total leads. Industry average for roofing is 8-15%, so {"you\'re performing well! 📈" if context['current_data'].get('conversion_rate', 0) > 8 else "there\'s room for improvement."}"

Always be helpful, accurate, and guide users toward successful outcomes!"""


def detect_action_intent(message: str) -> dict:
    """Detect if the user is requesting an action"""
    message_lower = message.lower()

    # Lead generation intent - check for various keywords
    lead_keywords = ['generate lead', 'create lead', 'add lead', 'make lead', 'new lead', 'get lead']
    if any(keyword in message_lower for keyword in lead_keywords):
        # Extract location from message
        import re
        # Look for city names in the message
        cities_pattern = r'(west\s+)?bloomfield(\s+hills?)?|birmingham|grosse\s+pointe|troy|rochester(\s+hills?)?|ann\s+arbor|michigan'
        match = re.search(cities_pattern, message_lower)
        location = match.group(0) if match else None

        # Extract count if specified
        count_match = re.search(r'(\d+)\s+(lead|new)', message_lower)
        count = int(count_match.group(1)) if count_match else 10

        return {
            "action": "generate_leads",
            "params": {
                "location": location,
                "count": min(count, 100)  # Cap at 100
            }
        }

    return {"action": None}


@bp.route('/chat', methods=['POST'])
def chat():
    """
    Process chat message and return AI response
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])

        if not user_message:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400

        # Check if this is an action request
        action_intent = detect_action_intent(user_message)

        if action_intent["action"] == "generate_leads":
            # Call the lead generation service directly
            try:
                location = action_intent["params"].get("location", "")
                count = action_intent["params"].get("count", 10)

                # Import required modules
                from app.database import get_db
                from app.services.intelligence.live_data_collector import run_live_collection
                import asyncio

                # Get database session and run collection
                db = next(get_db())
                try:
                    # Run async collection
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(run_live_collection(db, count))
                    loop.close()
                finally:
                    db.close()

                if results.get("success"):
                    ingested = results.get("ingested", 0)
                    location_text = f" for {location.title()}" if location else ""

                    response_text = f"✅ Successfully generated **{ingested} new leads**{location_text}!\n\n"

                    if location:
                        response_text += f"📍 **Note:** The leads are not location-filtered yet - this is a feature coming soon. The {ingested} leads generated are from the Southeast Michigan market.\n\n"

                    response_text += "You can view them in the **Leads Management** page."

                    return jsonify({
                        "success": True,
                        "response": response_text,
                        "action": "generate_leads",
                        "action_result": {
                            "statistics": {
                                "total_generated": results.get("total", 0),
                                "successfully_ingested": ingested,
                                "duplicates_skipped": results.get("skipped", 0)
                            }
                        },
                        "context": get_crm_context(),
                        "timestamp": datetime.utcnow().isoformat()
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "response": "❌ Failed to generate leads. Please try again or navigate to 'Live Data Generator' in the sidebar.",
                        "timestamp": datetime.utcnow().isoformat()
                    }), 200

            except Exception as e:
                logger.error(f"Error generating leads: {e}")
                return jsonify({
                    "success": False,
                    "response": f"❌ I encountered an error: {str(e)}\n\nPlease navigate to **Live Data Generator** in the sidebar to generate leads manually.",
                    "timestamp": datetime.utcnow().isoformat()
                }), 200

        # If OpenAI is not available, return helpful fallback
        if not OPENAI_AVAILABLE:
            return jsonify({
                "success": True,
                "response": "🤖 CRM Assistant is currently in basic mode. Here's what I can tell you:\n\n" +
                           f"• System Status: {get_crm_context()['current_data']}\n" +
                           "• For full AI assistance, please configure OpenAI API key.\n" +
                           "• You can navigate to different sections using the sidebar menu.",
                "context": get_crm_context(),
                "timestamp": datetime.utcnow().isoformat()
            }), 200

        # Build conversation messages for OpenAI
        messages = [
            {"role": "system", "content": get_system_prompt()}
        ]

        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            assistant_response = response.choices[0].message.content

            return jsonify({
                "success": True,
                "response": assistant_response,
                "context": get_crm_context(),
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }), 200

        except Exception as openai_error:
            # OpenAI failed, fall back to basic mode
            logger.warning(f"OpenAI API failed, using fallback: {str(openai_error)}")
            context = get_crm_context()
            current_data = context.get('current_data', {})

            # Provide helpful basic response
            fallback_text = "🤖 **CRM Assistant** (Basic Mode)\n\n"
            fallback_text += "**Current System Status:**\n"
            if current_data:
                fallback_text += f"• Total Leads: {current_data.get('total_leads', 0)}\n"
                fallback_text += f"• HOT Leads: {current_data.get('hot_leads', 0)}\n"
                fallback_text += f"• Customers: {current_data.get('total_customers', 0)}\n"
                fallback_text += f"• Projects: {current_data.get('total_projects', 0)}\n"
                fallback_text += f"• Conversion Rate: {current_data.get('conversion_rate', 0)}%\n\n"
            else:
                fallback_text += "• System operational\n\n"

            fallback_text += "💡 **Quick Actions:**\n"
            fallback_text += "• Navigate to **Leads Management** to view and manage leads\n"
            fallback_text += "• Navigate to **Customers Management** for customer details\n"
            fallback_text += "• Navigate to **Projects Management** to track projects\n\n"
            fallback_text += "📝 **Note:** Full AI assistance requires OpenAI API key configuration."

            return jsonify({
                "success": True,
                "response": fallback_text,
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "mode": "fallback"
            }), 200

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "fallback_response": "I'm having trouble processing your request right now. Please try again or navigate using the sidebar menu."
        }), 500


@bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    Get suggested questions/actions based on current CRM state
    """
    try:
        context = get_crm_context()
        current_data = context.get('current_data', {})

        suggestions = []

        # Dynamic suggestions based on CRM state
        if current_data.get('hot_leads', 0) > 0:
            suggestions.append({
                "text": f"Show me my {current_data['hot_leads']} HOT leads",
                "category": "leads",
                "priority": "high"
            })

        if current_data.get('total_leads', 0) > current_data.get('total_customers', 0) * 10:
            suggestions.append({
                "text": "How can I improve my conversion rate?",
                "category": "analytics",
                "priority": "medium"
            })

        suggestions.extend([
            {
                "text": "How do I add a new lead?",
                "category": "help",
                "priority": "low"
            },
            {
                "text": "Show me today's appointments",
                "category": "appointments",
                "priority": "medium"
            },
            {
                "text": "What's my revenue this month?",
                "category": "analytics",
                "priority": "medium"
            },
            {
                "text": "Guide me through creating a project",
                "category": "help",
                "priority": "low"
            }
        ])

        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/quick-actions', methods=['GET'])
def get_quick_actions():
    """
    Get quick action buttons based on user's common tasks
    """
    return jsonify({
        "success": True,
        "actions": [
            {
                "label": "Add New Lead",
                "icon": "👥",
                "page": "Leads_Management",
                "action": "add_lead"
            },
            {
                "label": "View HOT Leads",
                "icon": "🔥",
                "page": "Leads_Management",
                "action": "filter_hot"
            },
            {
                "label": "Add Customer",
                "icon": "🏢",
                "page": "Customers_Management",
                "action": "add_customer"
            },
            {
                "label": "Create Project",
                "icon": "🏗️",
                "page": "Projects_Management",
                "action": "add_project"
            },
            {
                "label": "Schedule Appointment",
                "icon": "📅",
                "page": "Appointments",
                "action": "add_appointment"
            },
            {
                "label": "View Analytics",
                "icon": "📊",
                "page": "Enhanced_Analytics",
                "action": "view_analytics"
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@bp.route('/context', methods=['GET'])
def get_context():
    """
    Get current CRM context for the assistant
    """
    try:
        context = get_crm_context()
        return jsonify({
            "success": True,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting context: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """
    CRM Assistant service health check
    """
    return jsonify({
        "status": "healthy",
        "service": "crm-assistant",
        "openai_available": OPENAI_AVAILABLE,
        "database_available": DB_AVAILABLE,
        "features": {
            "chat": "active",
            "suggestions": "active",
            "quick_actions": "active",
            "context_awareness": "active" if DB_AVAILABLE else "limited"
        },
        "timestamp": datetime.utcnow().isoformat()
    }), 200
