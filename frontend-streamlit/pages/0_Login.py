"""
Login & Sign Up Page
Supabase Authentication for iSwitch Roofs CRM
"""

import streamlit as st
from utils.supabase_auth import get_auth_client
import re

# Note: Page config is set in Home.py when using st.navigation()
# Individual pages should not call st.set_page_config()

# Custom CSS
st.markdown("""
<style>
    /* Center the login form */
    .main .block-container {
        max-width: 500px;
        padding-top: 2rem;
    }

    /* Logo styling */
    .login-logo {
        text-align: center;
        margin-bottom: 2rem;
    }

    .login-logo h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }

    /* Form styling */
    .stButton button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 1rem;
        font-weight: bold;
        margin-top: 1rem;
    }

    .stButton button:hover {
        opacity: 0.9;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
    }

    /* Success/Error messages */
    .success-box {
        padding: 1rem;
        border-radius: 8px;
        background: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }

    .error-box {
        padding: 1rem;
        border-radius: 8px;
        background: #f8d7da;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize auth client
auth = get_auth_client()

# Check if already authenticated
if auth.is_authenticated():
    st.success("✅ You are already logged in!")
    st.info("👉 Use the sidebar to navigate to the dashboard")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Go to Dashboard", use_container_width=True):
            st.switch_page("pages/0_Dashboard.py")
    with col2:
        if st.button("Logout", use_container_width=True):
            auth.sign_out()
            st.rerun()
    st.stop()

# Logo and title
st.markdown("""
<div class="login-logo">
    <h1>🏠 iSwitch Roofs</h1>
    <p style="color: #666; font-size: 1.1rem;">Premium CRM Platform</p>
</div>
""", unsafe_allow_html=True)

# Tabs for Login and Sign Up
tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up"])

# ============================================================================
# LOGIN TAB
# ============================================================================
with tab1:
    st.subheader("Welcome Back!")

    with st.form("login_form"):
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            remember_me = st.checkbox("Remember me", value=True)

        submit = st.form_submit_button("🔓 Login", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("⚠️ Please enter both email and password")
            else:
                with st.spinner("Authenticating..."):
                    result = auth.sign_in(email, password)

                    if result['success']:
                        st.success("✅ " + result['message'])
                        st.balloons()
                        st.info("Redirecting to dashboard...")
                        # Wait a moment to show success message
                        import time
                        time.sleep(1)
                        st.switch_page("pages/0_Dashboard.py")
                    else:
                        st.error("❌ " + result['error'])

    # Forgot password link
    st.markdown("---")
    if st.button("🔑 Forgot Password?", use_container_width=True):
        st.session_state.show_reset = True

    # Password reset dialog
    if st.session_state.get('show_reset', False):
        with st.form("reset_form"):
            st.write("**Reset Your Password**")
            reset_email = st.text_input(
                "Enter your email address",
                placeholder="your.email@example.com"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Send Reset Link"):
                    if reset_email:
                        result = auth.reset_password(reset_email)
                        if result['success']:
                            st.success("✅ " + result['message'])
                            st.session_state.show_reset = False
                        else:
                            st.error("❌ " + result['error'])
                    else:
                        st.error("⚠️ Please enter your email address")

            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_reset = False
                    st.rerun()

# ============================================================================
# SIGN UP TAB
# ============================================================================
with tab2:
    st.subheader("Create Your Account")

    with st.form("signup_form"):
        # User details
        full_name = st.text_input(
            "Full Name",
            placeholder="John Doe",
            key="signup_name"
        )

        signup_email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            key="signup_email"
        )

        col1, col2 = st.columns(2)
        with col1:
            signup_password = st.text_input(
                "Password",
                type="password",
                placeholder="Min. 6 characters",
                key="signup_password"
            )

        with col2:
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter password",
                key="confirm_password"
            )

        # Optional: Role selection
        role = st.selectbox(
            "Role",
            ["Sales Representative", "Manager", "Admin", "Other"],
            key="signup_role"
        )

        # Terms and conditions
        agree_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            key="agree_terms"
        )

        submit = st.form_submit_button("🚀 Create Account", use_container_width=True)

        if submit:
            # Validation
            errors = []

            if not full_name:
                errors.append("Please enter your full name")

            if not signup_email:
                errors.append("Please enter your email address")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", signup_email):
                errors.append("Please enter a valid email address")

            if not signup_password:
                errors.append("Please enter a password")
            elif len(signup_password) < 6:
                errors.append("Password must be at least 6 characters")

            if signup_password != confirm_password:
                errors.append("Passwords do not match")

            if not agree_terms:
                errors.append("Please agree to the Terms of Service")

            # Display errors or create account
            if errors:
                for error in errors:
                    st.error(f"⚠️ {error}")
            else:
                with st.spinner("Creating your account..."):
                    metadata = {
                        "full_name": full_name,
                        "role": role
                    }

                    result = auth.sign_up(signup_email, signup_password, metadata)

                    if result['success']:
                        st.success("✅ " + result['message'])
                        st.info("📧 Please check your email and click the verification link to activate your account.")
                        st.balloons()
                    else:
                        st.error("❌ " + result['error'])

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>
        <strong>iSwitch Roofs CRM</strong><br>
        Premium Lead Generation & Customer Management Platform<br>
        © 2025 iSwitch Roofs. All rights reserved.
    </p>
    <p style="font-size: 0.9rem; margin-top: 1rem;">
        Need help? Contact us at
        <a href="mailto:support@iswitchroofs.com">support@iswitchroofs.com</a>
    </p>
</div>
""", unsafe_allow_html=True)
