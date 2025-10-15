# Streamlit Authentication - Quick Start Guide

## 🚀 Start Using Authentication

Your Streamlit dashboard now has full Supabase authentication! Here's how to use it:

### 1️⃣ Start the Application

```bash
cd frontend-streamlit
streamlit run Home.py
```

### 2️⃣ Create Your First User

1. Open browser to `http://localhost:8501`
2. You'll see "Please log in" message
3. Click "🔐 Go to Login" button
4. Click "Sign Up" tab
5. Fill in your details:
   - Full Name: Your Name
   - Email: your.email@example.com
   - Password: (min 6 characters)
   - Role: Select your role
   - Check "I agree to Terms"
6. Click "Create Account"
7. Check your email for verification link
8. Click the verification link
9. Return to login page and sign in

### 3️⃣ Sign In

1. Enter your verified email and password
2. Click "Login"
3. You're in! 🎉

### 4️⃣ Navigate the Dashboard

- All pages now require authentication
- Your profile appears in the sidebar
- Click "Logout" to sign out anytime

## 📋 Key Features

✅ **Email/Password Authentication**  
✅ **Email Verification**  
✅ **Password Reset**  
✅ **Session Management**  
✅ **User Profiles**  
✅ **Role-Based Registration**  
✅ **Automatic Session Validation**  
✅ **Secure Logout**

## 🔐 Security Notes

- All passwords are securely hashed by Supabase
- Sessions use JWT tokens
- Sessions automatically expire after inactivity
- Email verification required for new accounts
- HTTPS enforced in production

## 🛠️ For Developers

### Protect a New Page

Add this to the top of any page:

```python
from utils.auth import require_auth

require_auth()
```

### Get User Information

```python
from utils.auth import get_current_user, get_user_email, get_user_metadata

user = get_current_user()
email = get_user_email()
metadata = get_user_metadata()
name = metadata.get('full_name', 'User')
```

### Customize Welcome Message

```python
from utils.auth import get_user_metadata

user_metadata = get_user_metadata()
user_name = user_metadata.get('full_name', 'User')

st.title(f"Welcome, {user_name}!")
```

## 🐛 Troubleshooting

**Can't access dashboard?**
- Make sure you're logged in
- Navigate to "Account > Login" in sidebar

**Not receiving verification email?**
- Check spam folder
- Verify email in Supabase dashboard

**Session keeps expiring?**
- Default timeout is 1 hour
- Configure in Supabase settings

## 📚 Full Documentation

See `AUTHENTICATION_IMPLEMENTATION.md` for complete details.

## 🎯 Next Steps

1. ✅ Test login/logout flow
2. ✅ Create admin user
3. Configure custom email templates
4. Implement role-based permissions
5. Add user management page

---

**Ready to use!** 🚀 Your dashboard is now secure with Supabase authentication.
