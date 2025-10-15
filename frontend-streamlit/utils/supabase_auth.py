"""
Supabase Authentication Client for Streamlit
Handles user authentication, session management, and user profiles
"""

import os
import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class SupabaseAuth:
    """Supabase authentication manager for Streamlit"""

    def __init__(self):
        """Initialize Supabase client with credentials from environment"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Missing Supabase credentials. "
                "Please set SUPABASE_URL and SUPABASE_KEY in .env file"
            )

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def sign_up(self, email: str, password: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a new user account

        Args:
            email: User's email address
            password: User's password (min 6 characters)
            metadata: Additional user metadata (name, role, etc.)

        Returns:
            Dict with success status and user data or error message
        """
        try:
            # Create user with email and password
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })

            if response.user:
                return {
                    "success": True,
                    "user": response.user,
                    "message": "Account created successfully! Please check your email to verify your account."
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create account. Please try again."
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in with email and password

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dict with success status and session data or error message
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.user and response.session:
                # Store session in Streamlit session state
                st.session_state.user = response.user
                st.session_state.session = response.session
                st.session_state.authenticated = True
                st.session_state.user_email = response.user.email
                st.session_state.user_id = response.user.id

                # Store user metadata if available
                if response.user.user_metadata:
                    st.session_state.user_metadata = response.user.user_metadata

                return {
                    "success": True,
                    "user": response.user,
                    "session": response.session,
                    "message": "Login successful!"
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid email or password"
                }

        except Exception as e:
            error_message = str(e)
            if "Invalid login credentials" in error_message:
                return {
                    "success": False,
                    "error": "Invalid email or password"
                }
            elif "Email not confirmed" in error_message:
                return {
                    "success": False,
                    "error": "Please verify your email address before signing in"
                }
            else:
                return {
                    "success": False,
                    "error": f"Login failed: {error_message}"
                }

    def sign_out(self) -> Dict[str, Any]:
        """
        Sign out the current user

        Returns:
            Dict with success status
        """
        try:
            self.client.auth.sign_out()

            # Clear Streamlit session state
            keys_to_clear = [
                'authenticated', 'user', 'session', 'user_email',
                'user_id', 'user_metadata', 'username'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]

            return {
                "success": True,
                "message": "Logged out successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently authenticated user from session state

        Returns:
            User object if authenticated, None otherwise
        """
        if st.session_state.get('authenticated') and st.session_state.get('user'):
            return st.session_state.user
        return None

    def get_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the current session

        Returns:
            Session object if authenticated, None otherwise
        """
        try:
            response = self.client.auth.get_session()
            if response:
                return response
        except Exception:
            pass
        return None

    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated

        Returns:
            True if authenticated, False otherwise
        """
        # Check session state first (fast)
        if st.session_state.get('authenticated'):
            # Verify session is still valid
            session = self.get_session()
            if session:
                return True
            else:
                # Session expired, clear state
                self.sign_out()
                return False
        return False

    def reset_password(self, email: str) -> Dict[str, Any]:
        """
        Send password reset email

        Args:
            email: User's email address

        Returns:
            Dict with success status
        """
        try:
            self.client.auth.reset_password_email(email)
            return {
                "success": True,
                "message": "Password reset email sent. Please check your inbox."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def update_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user metadata

        Args:
            data: Dictionary of user data to update

        Returns:
            Dict with success status
        """
        try:
            response = self.client.auth.update_user({"data": data})
            if response.user:
                st.session_state.user = response.user
                st.session_state.user_metadata = response.user.user_metadata
                return {
                    "success": True,
                    "user": response.user,
                    "message": "Profile updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update profile"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_user_metadata(self) -> Dict[str, Any]:
        """
        Get current user's metadata

        Returns:
            Dictionary of user metadata
        """
        if st.session_state.get('user_metadata'):
            return st.session_state.user_metadata

        user = self.get_current_user()
        if user and hasattr(user, 'user_metadata'):
            return user.user_metadata

        return {}


# Global instance
_auth_instance = None


def get_auth_client() -> SupabaseAuth:
    """
    Get singleton Supabase auth client instance

    Returns:
        SupabaseAuth: Authenticated Supabase client
    """
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = SupabaseAuth()
    return _auth_instance


def require_auth():
    """
    Decorator/middleware to require authentication for a page
    Redirects to login page if not authenticated
    """
    auth = get_auth_client()
    if not auth.is_authenticated():
        st.warning("⛔ Please log in to access this page")
        st.info("👉 Use the sidebar to navigate to the Login page")
        st.stop()


def check_session_validity():
    """
    Check if the current session is still valid
    Auto-logout if session expired
    """
    auth = get_auth_client()
    if st.session_state.get('authenticated'):
        session = auth.get_session()
        if not session:
            # Session expired
            auth.sign_out()
            st.warning("Your session has expired. Please log in again.")
            st.rerun()
