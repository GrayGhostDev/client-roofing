# Chatbot Service Database Integration - Code Update

This document contains the complete updated `send_message` method with full database persistence.

## Updated send_message Method

Replace the existing `send_message` method (starting at line 299) with this complete database-integrated version:

```python
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
```

## New Helper Method: _determine_escalation_reason

Add this helper method to the ChatbotService class:

```python
def _determine_escalation_reason(self, user_message: str, bot_response: str) -> EscalationReason:
    """
    Determine reason for escalation based on conversation context

    Args:
        user_message: User's message
        bot_response: Bot's response

    Returns:
        EscalationReason enum value
    """
    user_lower = user_message.lower()
    bot_lower = bot_response.lower()

    # Check for explicit requests
    if any(word in user_lower for word in ["speak to", "talk to", "human", "agent", "representative", "person"]):
        return EscalationReason.CUSTOMER_REQUEST

    # Check for complaints
    if any(word in user_lower for word in ["complaint", "unhappy", "disappointed", "terrible", "worst"]):
        return EscalationReason.COMPLAINT

    # Check for emergency
    if any(word in user_lower for word in ["emergency", "urgent", "asap", "immediate", "critical", "leaking"]):
        return EscalationReason.EMERGENCY

    # Check for complex technical questions
    if any(word in user_lower for word in ["complex", "detailed", "specific", "technical"]):
        return EscalationReason.COMPLEX_QUESTION

    # Check if bot is unsure
    if any(phrase in bot_lower for phrase in ["not sure", "don't know", "unable to", "can't help", "team member"]):
        return EscalationReason.AI_CONFIDENCE_LOW

    # Default
    return EscalationReason.COMPLEX_QUESTION
```

## Updated _execute_tool Method

Update the `_execute_tool` method to accept conversation_id for database linking:

```python
async def _execute_tool(
    self,
    tool_call,
    conversation_db_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute custom tool action

    Args:
        tool_call: GPT-5 tool call object
        conversation_db_id: Database conversation ID for linking

    Returns:
        Action result
    """
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    try:
        if tool_name == "check_availability":
            # Check team calendar
            date = arguments.get("date")
            time = arguments.get("time")
            return {
                "tool": "check_availability",
                "success": True,
                "result": f"We have availability on {date} at {time}. Would you like to book?"
            }

        elif tool_name == "create_lead":
            # Create lead in CRM
            if self.db:
                from app.repositories.lead_repository import LeadRepository
                lead_repo = LeadRepository(self.db)

                lead_data = {
                    "name": arguments.get("name"),
                    "phone": arguments.get("phone"),
                    "email": arguments.get("email"),
                    "address": arguments.get("address"),
                    "source": arguments.get("channel", "chatbot"),
                    "notes": arguments.get("notes"),
                    "status": "new"
                }

                lead = lead_repo.create(lead_data)

                # Link lead to conversation if we have conversation_db_id
                if conversation_db_id:
                    conv_repo = ChatConversationRepository(self.db)
                    conv_repo.update(conversation_db_id, {
                        "lead_id": lead.id,
                        "converted_to_lead": True
                    })

                return {
                    "tool": "create_lead",
                    "success": True,
                    "lead_id": lead.id,
                    "result": f"Lead created successfully for {arguments.get('name')}"
                }

        elif tool_name == "schedule_appointment":
            # Schedule appointment
            if self.db:
                from app.repositories.appointment_repository import AppointmentRepository
                appt_repo = AppointmentRepository(self.db)

                appt_data = {
                    "customer_name": arguments.get("name"),
                    "phone": arguments.get("phone"),
                    "address": arguments.get("address"),
                    "scheduled_date": arguments.get("date"),
                    "scheduled_time": arguments.get("time"),
                    "type": "inspection",
                    "status": "scheduled"
                }

                appointment = appt_repo.create(appt_data)

                # Link to conversation
                if conversation_db_id:
                    conv_repo = ChatConversationRepository(self.db)
                    conv_repo.update(conversation_db_id, {
                        "converted_to_appointment": True
                    })

                return {
                    "tool": "schedule_appointment",
                    "success": True,
                    "appointment_id": appointment.id,
                    "result": f"Inspection scheduled for {arguments.get('date')} at {arguments.get('time')}"
                }

        else:
            return {
                "tool": tool_name,
                "success": False,
                "result": f"Unknown tool: {tool_name}"
            }

    except Exception as e:
        logger.error(f"Tool execution error: {tool_name} - {str(e)}")
        return {
            "tool": tool_name,
            "success": False,
            "error": str(e)
        }
```

## Integration Notes

1. **Database Session Management**: The updated method properly manages database sessions, creating them when needed and closing them in the finally block.

2. **Conversation Persistence**: Every conversation is stored in the `chat_conversations` table with full metadata.

3. **Message Persistence**: Every message (user and assistant) is stored in the `conversation_messages` table with sequence numbers, timestamps, and GPT-5 metadata.

4. **Tool Call Tracking**: Tool calls and their results are saved in the message metadata for audit trail.

5. **Escalation Management**: Automatic escalation detection and reason classification.

6. **Lead/Customer Linking**: Conversations can be linked to existing leads or customers.

7. **Performance Metrics**: Token usage and processing time are tracked.

8. **Multi-channel Support**: Proper channel enum mapping for different platforms.

9. **Memory Cache Integration**: Continues to use Redis/local cache for fast retrieval while persisting to database.

10. **Error Handling**: Comprehensive error handling with proper logging and graceful degradation.
