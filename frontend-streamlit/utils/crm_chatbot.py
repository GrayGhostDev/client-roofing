"""
CRM Chatbot Component
Intelligent assistant for iSwitch Roofs CRM
"""

import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def get_api_base_url() -> str:
    """Get API base URL"""
    return st.session_state.get('api_base_url', 'http://localhost:8001')


def send_chat_message(message: str, history: List[Dict] = None) -> Dict:
    """
    Send chat message to CRM assistant API

    Args:
        message: User's message
        history: Conversation history

    Returns:
        API response dict
    """
    try:
        url = f"{get_api_base_url()}/api/crm-assistant/chat"
        payload = {
            "message": message,
            "history": history or []
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "fallback_response": "⏱️ The assistant is taking longer than expected. Please try again."
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Chat API error: {str(e)}")
        return {
            "success": False,
            "fallback_response": "🤖 I'm having trouble connecting right now. Please try again in a moment."
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "success": False,
            "fallback_response": "❌ An unexpected error occurred. Please refresh and try again."
        }


def get_suggestions() -> List[Dict]:
    """Get suggested questions/actions from API"""
    try:
        url = f"{get_api_base_url()}/api/crm-assistant/suggestions"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('suggestions', [])
    except Exception as e:
        logger.error(f"Error fetching suggestions: {str(e)}")
        return []


def get_quick_actions() -> List[Dict]:
    """Get quick action buttons from API"""
    try:
        url = f"{get_api_base_url()}/api/crm-assistant/quick-actions"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('actions', [])
    except Exception as e:
        logger.error(f"Error fetching quick actions: {str(e)}")
        return []


def render_chatbot_dialog():
    """
    Render the chatbot dialog box as a floating widget
    """
    # Initialize session state for chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False
    if 'show_suggestions' not in st.session_state:
        st.session_state.show_suggestions = True

    # Custom CSS for chat widget
    st.markdown("""
    <style>
    .chat-widget {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
    }

    .chat-toggle-button {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .chat-container {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 400px;
        height: 600px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        display: flex;
        flex-direction: column;
        z-index: 9998;
    }

    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 15px 15px 0 0;
        font-weight: bold;
        font-size: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 15px;
        background: #f5f5f5;
    }

    .chat-message {
        margin-bottom: 12px;
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 80%;
        word-wrap: break-word;
    }

    .chat-message-user {
        background: #667eea;
        color: white;
        margin-left: auto;
        text-align: right;
    }

    .chat-message-assistant {
        background: white;
        color: #333;
        border: 1px solid #e0e0e0;
    }

    .chat-input-area {
        padding: 15px;
        background: white;
        border-radius: 0 0 15px 15px;
        border-top: 1px solid #e0e0e0;
    }

    .suggestion-chip {
        display: inline-block;
        padding: 6px 12px;
        margin: 4px;
        background: #e8eaf6;
        color: #667eea;
        border-radius: 16px;
        font-size: 13px;
        cursor: pointer;
        border: 1px solid #c5cae9;
    }

    .suggestion-chip:hover {
        background: #667eea;
        color: white;
    }

    .quick-action-btn {
        display: inline-block;
        padding: 8px 16px;
        margin: 4px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        font-size: 13px;
        cursor: pointer;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # Chat toggle button (always visible)
    col1, col2, col3 = st.columns([6, 1, 1])

    with col3:
        if st.button("💬", key="chat_toggle", help="CRM Assistant"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()

    # Chat dialog (shown when open)
    if st.session_state.chat_open:
        with st.container():
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)

            # Chat header
            st.markdown("""
            <div class="chat-header">
                <span>🤖 CRM Assistant</span>
                <span style="font-size: 12px; opacity: 0.9;">AI-Powered</span>
            </div>
            """, unsafe_allow_html=True)

            # Messages area
            chat_container = st.container()
            with chat_container:
                # Display chat history
                for msg in st.session_state.chat_history:
                    role_class = "user" if msg["role"] == "user" else "assistant"
                    st.markdown(f"""
                    <div class="chat-message chat-message-{role_class}">
                        {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)

                # Show suggestions if no chat history
                if len(st.session_state.chat_history) == 0 and st.session_state.show_suggestions:
                    st.markdown("### 💡 Quick Start")
                    suggestions = get_suggestions()

                    for suggestion in suggestions[:4]:
                        if st.button(suggestion['text'], key=f"sug_{suggestion['text'][:20]}"):
                            handle_user_message(suggestion['text'])

                    st.markdown("---")
                    st.markdown("### ⚡ Quick Actions")
                    actions = get_quick_actions()

                    cols = st.columns(2)
                    for idx, action in enumerate(actions[:6]):
                        with cols[idx % 2]:
                            if st.button(f"{action['icon']} {action['label']}", key=f"act_{action['label']}"):
                                st.info(f"Navigate to: **{action['page']}** to {action['label']}")

            # Input area
            st.markdown("---")
            user_input = st.chat_input("Ask me anything about your CRM...", key="chat_input")

            if user_input:
                handle_user_message(user_input)

            st.markdown('</div>', unsafe_allow_html=True)


def handle_user_message(message: str):
    """Handle user message and get AI response"""
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": message
    })
    st.session_state.show_suggestions = False

    # Get AI response
    with st.spinner("🤔 Thinking..."):
        response = send_chat_message(message, st.session_state.chat_history)

    # Add assistant response to history
    if response.get('success'):
        assistant_message = response.get('response', 'I apologize, but I couldn\'t process that.')
    else:
        assistant_message = response.get('fallback_response', 'Sorry, I encountered an error.')

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    # Rerun to update UI
    st.rerun()


def render_compact_chatbot():
    """
    Render a compact inline chatbot widget for the dashboard
    """
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    st.markdown("""
    <style>
    .compact-chat {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 20px 0;
    }
    .compact-chat-header {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .compact-chat-subtitle {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("""
        <div class="compact-chat">
            <div class="compact-chat-header">🤖 CRM Assistant</div>
            <div class="compact-chat-subtitle">Ask me anything about leads, customers, projects, or analytics!</div>
        </div>
        """, unsafe_allow_html=True)

        # Quick suggestions
        st.markdown("### 💡 Try asking:")
        cols = st.columns(3)

        suggestions = [
            "How many hot leads do I have?",
            "What's my conversion rate?",
            "Show me today's appointments"
        ]

        for idx, suggestion in enumerate(suggestions):
            with cols[idx]:
                if st.button(suggestion, key=f"quick_sug_{idx}", use_container_width=True):
                    handle_user_message(suggestion)

        # Chat input
        user_input = st.chat_input("💬 Ask your CRM assistant...", key="compact_chat_input")

        if user_input:
            handle_user_message(user_input)

        # Show recent chat
        if st.session_state.chat_history:
            with st.expander("💬 Recent Conversation", expanded=True):
                for msg in st.session_state.chat_history[-4:]:
                    if msg["role"] == "user":
                        st.markdown(f"**You:** {msg['content']}")
                    else:
                        st.markdown(f"**Assistant:** {msg['content']}")

                if st.button("Clear Chat History", key="clear_chat"):
                    st.session_state.chat_history = []
                    st.session_state.show_suggestions = True
                    st.rerun()
