# 🔍 AI Search - Quick Start Guide

**Get started with AI-powered search in 5 minutes!**

---

## 🚀 Quick Start

### Step 1: Start the Backend (if not running)
```bash
cd backend
python main.py
```

**Expected**: Backend starts on http://localhost:8001

---

### Step 2: Start Streamlit (if not running)
```bash
cd frontend-streamlit
streamlit run Home.py
```

**Expected**: Dashboard opens at http://localhost:8501

---

### Step 3: Access AI Search
1. Open browser: http://localhost:8501
2. Click **"🔍 AI Search"** in sidebar menu
3. See the AI search interface

---

### Step 4: Try Your First Search

**Option A - Quick Action (Easiest)**
1. Click any quick action button
2. For example: **"🔥 Hot Leads Today"**
3. See instant results!

**Option B - Natural Language**
1. Type in search box: `Show me all leads from this week`
2. Click **"🔍 Search"**
3. See AI-interpreted results!

**Option C - Use Example**
1. Scroll to "Example Searches" section
2. Click on any example query
3. Query auto-populates, click Search!

---

## 📝 Try These Example Queries

```
Show me all hot leads from this week
Find customers in Bloomfield Hills
List active projects over $100k
Get calls with negative sentiment from today
Show appointments for today
```

---

## 🎯 What You Can Search For

| Entity | Example Query |
|--------|---------------|
| **Leads** | "Show me qualified leads with high scores" |
| **Customers** | "Find all premium tier customers" |
| **Projects** | "List completed projects from last month" |
| **Voice Calls** | "Get calls that were escalated to human" |
| **Chatbot** | "Show chat conversations from today" |
| **Appointments** | "Find scheduled inspections this week" |

---

## ✨ Key Features

### 1. Natural Language Understanding
Just ask your question naturally:
- ✅ "Show me hot leads from this week"
- ✅ "Find customers with projects over $50k"
- ✅ "List calls with negative sentiment"

### 2. Quick Actions
One-click predefined searches:
- 🔥 Hot Leads Today
- 📬 New Leads This Week
- 🏗️ Active Projects
- 📅 Today's Appointments

### 3. Search History
- See your last 10 searches
- Repeat any previous search
- Track what you've searched for

---

## 🔧 API Endpoints Created

All accessible at http://localhost:8001:

```
POST   /api/ai-search/search          # Main search endpoint
POST   /api/ai-search/suggest         # Query suggestions
GET    /api/ai-search/examples        # Example queries
GET    /api/ai-search/quick-actions   # Quick action buttons
GET    /api/ai-search/health          # Health check
```

---

## 📁 Files Created

### Backend
- `backend/app/services/ai_search_service.py` (500+ lines) - AI search engine
- `backend/app/routes/ai_search.py` (300+ lines) - API routes
- `backend/app/__init__.py` - Blueprint registration added

### Frontend
- `frontend-streamlit/pages/14_🔍_AI_Search.py` (400+ lines) - User interface

### Documentation
- `AI_SEARCH_WORKFLOW_GUIDE.md` (800+ lines) - Complete guide
- `AI_SEARCH_QUICK_START.md` (This file) - Quick start

**Total**: 2,000+ lines of code and documentation

---

## 🧪 Quick Test

Test the health endpoint:
```bash
curl http://localhost:8001/api/ai-search/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "ai-search",
  "openai_configured": true,
  "model": "gpt-4o",
  "features": [...]
}
```

---

## 🎉 You're Ready!

The AI-powered search system is now available:
- ✅ Natural language query processing
- ✅ GPT-4o intent understanding
- ✅ Multi-entity search (leads, customers, projects, etc.)
- ✅ Quick actions for common searches
- ✅ Search examples and history
- ✅ Beautiful Streamlit interface

---

## 💡 Pro Tips

1. **Be Specific**: Include time frames ("this week", "today")
2. **Use Natural Language**: Write how you would ask a person
3. **Try Quick Actions**: Fastest way to get results
4. **Check AI Interpretation**: See how AI understood your query
5. **Use Search History**: Quickly repeat searches

---

## 📚 Need Help?

- **Full Guide**: See [AI_SEARCH_WORKFLOW_GUIDE.md](AI_SEARCH_WORKFLOW_GUIDE.md)
- **API Docs**: Check backend/app/routes/ai_search.py
- **Examples**: In-app examples on AI Search page

---

*Quick Start Guide - Created 2025-10-12*
*Ready to search your CRM data with AI!* 🚀
