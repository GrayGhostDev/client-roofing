"""
Conversation API Routes for Voice AI and Chatbot
Flask REST endpoints for all conversational AI features

Endpoints:
- Voice interaction management
- Chatbot messaging
- Sentiment analysis
- Conversation analytics
- Performance metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.integrations.chatbot import chatbot_service
from app.integrations.voice_ai import voice_ai_service
from app.models.voice_interaction import (
    AppointmentBookingRequest,
    CallTransfer,
    VoiceConfiguration,
    VoiceInteractionCreate,
)
from app.services.intelligence.conversation_analytics import conversation_analytics_service
from app.services.intelligence.sentiment_analysis import sentiment_analysis_service
from app.utils.auth import require_auth

logger = logging.getLogger(__name__)
bp = Blueprint("conversation", __name__)


# ============================================================================
# VOICE AI ENDPOINTS
# ============================================================================

@bp.route("/voice/call/incoming", methods=["POST"])
@require_auth
async def handle_incoming_call():
    """
    Handle incoming voice call with AI assistant

    Request Body:
        {
            "phone_number": "+1-248-555-0123",
            "caller_name": "John Smith" (optional),
            "call_id": "unique_call_id" (optional)
        }

    Returns:
        201: Voice interaction created
        400: Invalid request
        500: Server error

    Example:
        POST /api/conversation/voice/call/incoming
        {
            "phone_number": "+1-248-555-0123",
            "caller_name": "John Smith"
        }
    """
    try:
        data = request.get_json()

        phone_number = data.get("phone_number")
        if not phone_number:
            return jsonify({"error": "phone_number is required"}), 400

        caller_name = data.get("caller_name")
        call_id = data.get("call_id")

        # Process call with voice AI
        interaction = await voice_ai_service.handle_inbound_call(
            phone_number=phone_number,
            caller_name=caller_name,
            call_id=call_id
        )

        return jsonify({
            "success": True,
            "interaction": interaction.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }), 201

    except Exception as e:
        logger.error(f"Incoming call error: {str(e)}")
        return jsonify({"error": "Failed to process incoming call", "details": str(e)}), 500


@bp.route("/voice/call/<interaction_id>/analyze", methods=["POST"])
@require_auth
async def analyze_call_quality(interaction_id: str):
    """
    Analyze call quality and extract insights using GPT-5

    Path Parameters:
        interaction_id: Voice interaction ID

    Request Body:
        {
            "transcript": "Full call transcript",
            "duration_seconds": 180
        }

    Returns:
        200: Call analysis
        400: Invalid request
        404: Interaction not found
        500: Server error
    """
    try:
        data = request.get_json()

        transcript = data.get("transcript")
        duration_seconds = data.get("duration_seconds", 0)

        if not transcript:
            return jsonify({"error": "transcript is required"}), 400

        # Analyze call quality
        analysis = await voice_ai_service.analyze_call_quality(
            interaction_id=interaction_id,
            transcript=transcript,
            duration_seconds=duration_seconds
        )

        return jsonify({
            "success": True,
            "analysis": analysis.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Call analysis error: {str(e)}")
        return jsonify({"error": "Call analysis failed", "details": str(e)}), 500


@bp.route("/voice/appointment/schedule", methods=["POST"])
@require_auth
async def schedule_appointment_voice():
    """
    Schedule appointment from voice interaction

    Request Body:
        {
            "caller_name": "John Smith",
            "phone_number": "+1-248-555-0123",
            "email": "john@example.com" (optional),
            "property_address": "123 Main St, Birmingham, MI",
            "preferred_date": "2025-10-15",
            "preferred_time": "14:00",
            "service_type": "roof inspection",
            "notes": "Storm damage" (optional),
            "urgency": "high",
            "flow_id": "call_123456"
        }

    Returns:
        201: Appointment scheduled
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        try:
            booking_request = AppointmentBookingRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Invalid appointment data", "details": e.errors()}), 400

        flow_id = data.get("flow_id", "unknown")

        # Schedule appointment
        result = await voice_ai_service.schedule_appointment_from_call(
            booking_request=booking_request,
            flow_id=flow_id
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify({
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }), 201

    except Exception as e:
        logger.error(f"Appointment scheduling error: {str(e)}")
        return jsonify({"error": "Appointment scheduling failed", "details": str(e)}), 500


@bp.route("/voice/call/transfer", methods=["POST"])
@require_auth
async def transfer_call_to_human():
    """
    Transfer call to human agent

    Request Body:
        {
            "interaction_id": "call_123456",
            "agent_id": "agent_001" (optional),
            "department": "sales",
            "reason": "Complex pricing question",
            "context_summary": "Customer wants quote for 3000 sqft roof",
            "customer_sentiment": "positive",
            "priority": "high"
        }

    Returns:
        200: Transfer initiated
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        try:
            transfer_request = CallTransfer(**data)
        except ValidationError as e:
            return jsonify({"error": "Invalid transfer data", "details": e.errors()}), 400

        # TODO: Integrate with actual call routing system
        logger.info(f"Call transfer requested: {transfer_request.model_dump()}")

        return jsonify({
            "success": True,
            "message": "Call transfer initiated",
            "transfer_id": f"transfer_{datetime.utcnow().timestamp()}",
            "estimated_wait_seconds": 30,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Call transfer error: {str(e)}")
        return jsonify({"error": "Call transfer failed", "details": str(e)}), 500


@bp.route("/voice/config", methods=["GET", "PUT"])
@require_auth
async def voice_configuration():
    """
    Get or update voice AI configuration

    GET - Retrieve current configuration
    PUT - Update configuration

    Request Body (PUT only):
        VoiceConfiguration model fields

    Returns:
        200: Configuration retrieved/updated
        400: Invalid configuration
        500: Server error
    """
    try:
        if request.method == "GET":
            config = voice_ai_service.config
            return jsonify({
                "success": True,
                "configuration": config.model_dump(),
                "timestamp": datetime.utcnow().isoformat()
            }), 200

        elif request.method == "PUT":
            data = request.get_json()

            try:
                new_config = VoiceConfiguration(**data)
                voice_ai_service.config = new_config

                return jsonify({
                    "success": True,
                    "message": "Configuration updated",
                    "configuration": new_config.model_dump(),
                    "timestamp": datetime.utcnow().isoformat()
                }), 200

            except ValidationError as e:
                return jsonify({"error": "Invalid configuration", "details": e.errors()}), 400

    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        return jsonify({"error": "Configuration operation failed", "details": str(e)}), 500


# ============================================================================
# CHATBOT ENDPOINTS
# ============================================================================

@bp.route("/chatbot/message", methods=["POST"])
@require_auth
async def send_chatbot_message():
    """
    Send message to chatbot and get AI response

    Request Body:
        {
            "conversation_id": "conv_123456",
            "message": "What does a roof inspection cost?",
            "user_id": "user_001" (optional),
            "channel": "website",
            "image_url": "https://..." (optional for photo analysis),
            "metadata": {...} (optional)
        }

    Returns:
        200: Bot response
        400: Invalid request
        500: Server error

    Example:
        POST /api/conversation/chatbot/message
        {
            "conversation_id": "conv_abc123",
            "message": "I need a roof inspection",
            "channel": "website"
        }
    """
    try:
        data = request.get_json()

        conversation_id = data.get("conversation_id")
        message = data.get("message")

        if not conversation_id or not message:
            return jsonify({"error": "conversation_id and message are required"}), 400

        user_id = data.get("user_id")
        channel = data.get("channel", "website")
        image_url = data.get("image_url")
        metadata = data.get("metadata")

        # Process message with chatbot
        response = await chatbot_service.send_message(
            conversation_id=conversation_id,
            message=message,
            user_id=user_id,
            channel=channel,
            image_url=image_url,
            metadata=metadata
        )

        return jsonify({
            "success": True,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Chatbot message error: {str(e)}")
        return jsonify({"error": "Message processing failed", "details": str(e)}), 500


@bp.route("/chatbot/photo/analyze", methods=["POST"])
@require_auth
async def analyze_roof_photo():
    """
    Analyze roof damage from photo using GPT-5 vision

    Request Body:
        {
            "conversation_id": "conv_123456",
            "image_data": "base64_encoded_image" or "image_url",
            "image_format": "base64" or "url"
        }

    Returns:
        200: Photo analysis
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        conversation_id = data.get("conversation_id")
        image_data = data.get("image_data")

        if not conversation_id or not image_data:
            return jsonify({"error": "conversation_id and image_data are required"}), 400

        image_format = data.get("image_format", "base64")

        # Analyze photo with GPT-5 vision
        analysis = await chatbot_service.analyze_roof_photo(
            conversation_id=conversation_id,
            image_data=image_data,
            image_format=image_format
        )

        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Photo analysis error: {str(e)}")
        return jsonify({"error": "Photo analysis failed", "details": str(e)}), 500


@bp.route("/chatbot/conversation/<conversation_id>", methods=["GET", "DELETE"])
@require_auth
async def manage_conversation(conversation_id: str):
    """
    Get or delete conversation

    GET - Retrieve conversation history
    DELETE - Clear conversation and reset context

    Path Parameters:
        conversation_id: Conversation identifier

    Query Parameters (GET only):
        limit: Maximum messages to retrieve (default: 20)

    Returns:
        200: Conversation data or cleared successfully
        404: Conversation not found
        500: Server error
    """
    try:
        if request.method == "GET":
            limit = int(request.args.get("limit", 20))

            history = await chatbot_service.memory.get_conversation_history(
                conversation_id=conversation_id,
                limit=limit
            )

            return jsonify({
                "success": True,
                "conversation_id": conversation_id,
                "message_count": len(history),
                "messages": history,
                "timestamp": datetime.utcnow().isoformat()
            }), 200

        elif request.method == "DELETE":
            await chatbot_service.memory.clear_conversation(conversation_id)

            return jsonify({
                "success": True,
                "message": "Conversation cleared",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }), 200

    except Exception as e:
        logger.error(f"Conversation management error: {str(e)}")
        return jsonify({"error": "Conversation operation failed", "details": str(e)}), 500


# ============================================================================
# SENTIMENT ANALYSIS ENDPOINTS
# ============================================================================

@bp.route("/sentiment/analyze", methods=["POST"])
@require_auth
async def analyze_sentiment():
    """
    Analyze sentiment of text using GPT-5

    Request Body:
        {
            "text": "Text to analyze",
            "context": {...} (optional),
            "source": "conversation|email|sms|call"
        }

    Returns:
        200: Sentiment analysis
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        text = data.get("text")
        if not text:
            return jsonify({"error": "text is required"}), 400

        context = data.get("context")
        source = data.get("source", "conversation")

        # Analyze sentiment
        analysis = await sentiment_analysis_service.analyze_text(
            text=text,
            context=context,
            source=source
        )

        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Sentiment analysis error: {str(e)}")
        return jsonify({"error": "Sentiment analysis failed", "details": str(e)}), 500


@bp.route("/sentiment/thread/<conversation_id>/analyze", methods=["POST"])
@require_auth
async def analyze_conversation_sentiment():
    """
    Analyze sentiment across entire conversation thread

    Path Parameters:
        conversation_id: Conversation identifier

    Request Body:
        {
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

    Returns:
        200: Thread sentiment analysis
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        messages = data.get("messages", [])
        if not messages:
            return jsonify({"error": "messages array is required"}), 400

        # Analyze thread
        analysis = await sentiment_analysis_service.analyze_conversation_thread(
            messages=messages,
            conversation_id=conversation_id
        )

        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Thread sentiment analysis error: {str(e)}")
        return jsonify({"error": "Thread analysis failed", "details": str(e)}), 500


@bp.route("/sentiment/buying-signals", methods=["POST"])
@require_auth
async def detect_buying_signals():
    """
    Detect buying signals in customer message using GPT-5

    Request Body:
        {
            "text": "Customer message text"
        }

    Returns:
        200: Detected buying signals
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        text = data.get("text")
        if not text:
            return jsonify({"error": "text is required"}), 400

        # Detect buying signals
        signals = await sentiment_analysis_service.detect_buying_signals(text)

        return jsonify({
            "success": True,
            "buying_signals": signals,
            "count": len(signals),
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Buying signal detection error: {str(e)}")
        return jsonify({"error": "Buying signal detection failed", "details": str(e)}), 500


@bp.route("/sentiment/satisfaction", methods=["POST"])
@require_auth
async def assess_satisfaction():
    """
    Assess customer satisfaction from interaction using GPT-5

    Request Body:
        {
            "interaction_text": "Full interaction text",
            "interaction_type": "conversation|call|email"
        }

    Returns:
        200: Satisfaction assessment with CSAT/NPS scores
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        interaction_text = data.get("interaction_text")
        if not interaction_text:
            return jsonify({"error": "interaction_text is required"}), 400

        interaction_type = data.get("interaction_type", "conversation")

        # Assess satisfaction
        assessment = await sentiment_analysis_service.assess_customer_satisfaction(
            interaction_text=interaction_text,
            interaction_type=interaction_type
        )

        return jsonify({
            "success": True,
            "assessment": assessment,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Satisfaction assessment error: {str(e)}")
        return jsonify({"error": "Satisfaction assessment failed", "details": str(e)}), 500


# ============================================================================
# CONVERSATION ANALYTICS ENDPOINTS
# ============================================================================

@bp.route("/analytics/conversation/<conversation_id>/quality", methods=["POST"])
@require_auth
async def analyze_conversation_quality():
    """
    Comprehensive conversation quality analysis using GPT-5

    Path Parameters:
        conversation_id: Conversation identifier

    Request Body:
        {
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "metadata": {...} (optional)
        }

    Returns:
        200: Quality analysis with scores
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        conversation_id = request.view_args.get("conversation_id")
        messages = data.get("messages", [])
        metadata = data.get("metadata")

        if not messages:
            return jsonify({"error": "messages array is required"}), 400

        # Analyze quality
        analysis = await conversation_analytics_service.analyze_conversation_quality(
            conversation_id=conversation_id,
            messages=messages,
            metadata=metadata
        )

        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Quality analysis error: {str(e)}")
        return jsonify({"error": "Quality analysis failed", "details": str(e)}), 500


@bp.route("/analytics/topics", methods=["POST"])
@require_auth
async def extract_topics_intents():
    """
    Extract topics and intents from multiple conversations using GPT-5

    Request Body:
        {
            "conversations": [
                {
                    "conversation_id": "conv_001",
                    "messages": [...],
                    "created_at": "2025-10-01T..."
                }
            ],
            "timeframe_days": 30
        }

    Returns:
        200: Topic and intent analysis
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        conversations = data.get("conversations", [])
        timeframe_days = data.get("timeframe_days", 30)

        if not conversations:
            return jsonify({"error": "conversations array is required"}), 400

        # Extract topics
        analysis = await conversation_analytics_service.extract_topics_and_intents(
            conversations=conversations,
            timeframe_days=timeframe_days
        )

        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Topic extraction error: {str(e)}")
        return jsonify({"error": "Topic extraction failed", "details": str(e)}), 500


@bp.route("/analytics/conversion/<conversation_id>", methods=["POST"])
@require_auth
async def analyze_conversion_path():
    """
    Analyze conversation conversion path using GPT-5

    Path Parameters:
        conversation_id: Conversation identifier

    Request Body:
        {
            "messages": [...],
            "outcome": "converted|lost|pending",
            "metadata": {...} (optional)
        }

    Returns:
        200: Conversion path analysis
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        conversation_id = request.view_args.get("conversation_id")
        messages = data.get("messages", [])
        outcome = data.get("outcome", "pending")
        metadata = data.get("metadata")

        if not messages:
            return jsonify({"error": "messages array is required"}), 400

        # Analyze conversion path
        analysis = await conversation_analytics_service.analyze_conversion_path(
            conversation_id=conversation_id,
            messages=messages,
            outcome=outcome,
            metadata=metadata
        )

        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Conversion path analysis error: {str(e)}")
        return jsonify({"error": "Conversion analysis failed", "details": str(e)}), 500


@bp.route("/analytics/agent/<agent_id>/performance", methods=["POST"])
@require_auth
async def analyze_agent_performance():
    """
    Analyze individual agent performance using GPT-5

    Path Parameters:
        agent_id: Agent identifier

    Request Body:
        {
            "conversations": [
                {
                    "conversation_id": "...",
                    "messages": [...],
                    "resolved": true
                }
            ],
            "timeframe_days": 30
        }

    Returns:
        200: Agent performance analysis
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        agent_id = request.view_args.get("agent_id")
        conversations = data.get("conversations", [])
        timeframe_days = data.get("timeframe_days", 30)

        if not conversations:
            return jsonify({"error": "conversations array is required"}), 400

        # Analyze agent performance
        analysis = await conversation_analytics_service.analyze_agent_performance(
            agent_id=agent_id,
            conversations=conversations,
            timeframe_days=timeframe_days
        )

        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Agent performance analysis error: {str(e)}")
        return jsonify({"error": "Performance analysis failed", "details": str(e)}), 500


@bp.route("/analytics/insights", methods=["POST"])
@require_auth
async def generate_insights():
    """
    Generate actionable insights from conversation data using GPT-5

    Request Body:
        {
            "conversations": [...],
            "focus_area": "sales|support|quality" (optional)
        }

    Returns:
        200: Business insights and recommendations
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        conversations = data.get("conversations", [])
        focus_area = data.get("focus_area")

        if not conversations:
            return jsonify({"error": "conversations array is required"}), 400

        # Generate insights
        insights = await conversation_analytics_service.generate_conversation_insights(
            conversations=conversations,
            focus_area=focus_area
        )

        return jsonify({
            "success": True,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Insights generation error: {str(e)}")
        return jsonify({"error": "Insights generation failed", "details": str(e)}), 500


@bp.route("/analytics/metrics", methods=["POST"])
@require_auth
async def calculate_metrics():
    """
    Calculate comprehensive conversation metrics

    Request Body:
        {
            "conversations": [...],
            "start_date": "2025-10-01",
            "end_date": "2025-10-31"
        }

    Returns:
        200: Comprehensive metrics dashboard
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        conversations = data.get("conversations", [])
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")

        if not all([conversations, start_date_str, end_date_str]):
            return jsonify({"error": "conversations, start_date, and end_date are required"}), 400

        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        # Calculate metrics
        metrics = await conversation_analytics_service.calculate_conversation_metrics(
            conversations=conversations,
            start_date=start_date,
            end_date=end_date
        )

        return jsonify({
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except ValueError as e:
        return jsonify({"error": "Invalid date format", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Metrics calculation error: {str(e)}")
        return jsonify({"error": "Metrics calculation failed", "details": str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check for conversation services

    Returns:
        200: All services healthy
        503: Service degraded
    """
    try:
        status = {
            "voice_ai": "healthy",
            "chatbot": "healthy",
            "sentiment_analysis": "healthy",
            "conversation_analytics": "healthy"
        }

        return jsonify({
            "status": "healthy",
            "services": status,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503
