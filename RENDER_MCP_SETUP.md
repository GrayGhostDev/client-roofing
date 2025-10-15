# Render MCP Server Setup Guide

## Overview

The Render MCP (Model Context Protocol) server enables Claude Code to directly manage your Render infrastructure, including setting environment variables programmatically.

## Setup Steps

### Step 1: Create Render API Key

1. **Go to Render API Keys page:**
   ```
   https://dashboard.render.com/settings#api-keys
   ```

2. **Click "Create API Key"**
   - Name: `Claude Code MCP`
   - Description: `MCP server for automated deployment`

3. **Copy the API key** (you'll need it in the next step)

### Step 2: Configure Claude Code MCP Server

Run this command to add the Render MCP server:

```bash
claude mcp add render https://mcp.render.com/mcp \
  --header "Authorization: Bearer YOUR_API_KEY_HERE"
```

Replace `YOUR_API_KEY_HERE` with the API key you just created.

### Step 3: Verify Configuration

```bash
# List MCP servers
claude mcp list

# Should show:
# render - https://mcp.render.com/mcp
```

### Step 4: Use Render MCP Commands

Once configured, Claude Code can directly manage your Render services:

```bash
# Example prompts you can use:
"Set my Render workspace to iswitch-roofs"
"List all my Render services"
"Set environment variable DATABASE_URL for service srv-d3mlmmur433s73abuar0"
"Deploy service srv-d3mlmmur433s73abuar0"
"Show logs for iswitch-roofs-api service"
```

## Automated Environment Variable Setup

Once the MCP server is configured, I can automatically set all required environment variables:

### Variables to Set

From your `.env` file, these need to be configured in Render:

```bash
DATABASE_URL=postgresql://postgres.tdwpzktihdeu...
SUPABASE_URL=https://tdwpzktihdeuza...
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5...
```

### Automated Script (After MCP Setup)

Once MCP is configured, Claude Code can run:

```bash
# This will work after MCP is configured
claude --mcp render "Set environment variables for service srv-d3mlmmur433s73abuar0:
  - DATABASE_URL from .env
  - SUPABASE_URL from .env
  - SUPABASE_KEY from .env
  - SUPABASE_SERVICE_ROLE_KEY from .env (named SUPABASE_SERVICE_KEY locally)"
```

## Alternative: Manual Dashboard Method

If you prefer not to set up MCP, you can still set variables manually:

1. Go to: https://dashboard.render.com/web/srv-d3mlmmur433s73abuar0
2. Click "Environment" tab
3. Add each variable manually
4. Save (triggers automatic redeploy)

## Benefits of Using MCP

✅ **Automated Deployment**
- Set environment variables programmatically
- No manual dashboard clicks
- Repeatable and scriptable

✅ **Infrastructure as Code**
- Manage all Render resources via Claude Code
- Version control your deployment commands
- Easy to replicate across environments

✅ **Real-time Monitoring**
- Query service metrics
- Retrieve logs instantly
- Check deployment status

✅ **Database Management**
- Query databases directly
- Analyze performance
- Manage backups

## Security Considerations

⚠️ **API Key Security:**
- Store API key securely (not in git)
- Rotate keys periodically
- Limit key scope to necessary permissions only

⚠️ **Environment Variables:**
- Never commit `.env` files with secrets
- Use `.env.example` for templates
- Verify variables are set correctly before deployment

## Troubleshooting

### MCP Server Not Responding

```bash
# Check MCP configuration
claude mcp list

# Remove and re-add
claude mcp remove render
claude mcp add render https://mcp.render.com/mcp \
  --header "Authorization: Bearer YOUR_API_KEY"
```

### Authorization Errors

- Verify API key is correct
- Check key hasn't expired
- Ensure key has proper permissions in Render dashboard

### Cannot Find Service

```bash
# First set workspace
"Set my Render workspace to [YOUR_WORKSPACE_NAME]"

# Then list services to verify
"List all Render services in my workspace"
```

## Next Steps

After configuring Render MCP server:

1. ✅ MCP server configured
2. ✅ API key verified
3. ✅ Workspace set
4. ✅ Environment variables set via MCP
5. ✅ Service redeployed automatically
6. ✅ Backend health check passes
7. ✅ Update Streamlit secrets
8. ✅ Full stack operational

## Quick Reference

### MCP Configuration File Location

- **macOS/Linux:** `~/.claude/mcp.json`
- **Manual edit:** Add to `mcpServers` section

```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### Useful MCP Commands

```bash
# Service management
"List all my Render services"
"Deploy service [SERVICE_NAME]"
"Show logs for [SERVICE_NAME]"
"Get service details for srv-d3mlmmur433s73abuar0"

# Environment variables
"Set environment variable [KEY]=[VALUE] for service [NAME]"
"List environment variables for service [NAME]"

# Database operations
"Query database [DB_NAME]: SELECT * FROM leads LIMIT 5"
"Show database metrics for [DB_NAME]"

# Monitoring
"What was the busiest traffic day for my service this month?"
"Show autoscaling behavior for [SERVICE_NAME]"
"Get performance metrics for srv-d3mlmmur433s73abuar0"
```

## Documentation Links

- **Render MCP Docs:** https://render.com/docs/mcp-server
- **Render API Keys:** https://dashboard.render.com/settings#api-keys
- **Render Dashboard:** https://dashboard.render.com/
- **Your Service:** https://dashboard.render.com/web/srv-d3mlmmur433s73abuar0

---

**Current Status:** Waiting for Render API key to configure MCP server

**Action Required:** Create API key at https://dashboard.render.com/settings#api-keys

**Time to Complete:** 2-3 minutes + automated deployment via MCP
