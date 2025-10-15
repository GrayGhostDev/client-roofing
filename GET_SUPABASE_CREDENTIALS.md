# Get Supabase Production Credentials

## ⚠️ Critical Issue Detected

Your `.env` file currently has **LOCAL development URLs**:
- `SUPABASE_URL=http://127.0.0.1:54321` (local)
- `DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/iswitch_crm` (local)

For production deployment to Render, you need **CLOUD Supabase URLs**.

## Step-by-Step Guide

### Step 1: Access Your Supabase Project

Go to: **https://supabase.com/dashboard**

- If you already have a project named "iswitch_crm" or similar, select it
- If not, you need to create a new project first

### Step 2: Get API Credentials

1. **Go to Settings → API:**
   ```
   https://supabase.com/dashboard/project/[YOUR-PROJECT-ID]/settings/api
   ```

2. **Copy these values:**

   **Project URL** (looks like):
   ```
   https://[project-id].supabase.co
   ```
   → This goes in `SUPABASE_URL`

   **anon public key** (starts with `eyJhbGci`):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
   ```
   → This goes in `SUPABASE_KEY`

   **service_role key** (starts with `eyJhbGci`):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
   ```
   → This goes in `SUPABASE_SERVICE_KEY`

### Step 3: Get Database Connection String

1. **Go to Settings → Database:**
   ```
   https://supabase.com/dashboard/project/[YOUR-PROJECT-ID]/settings/database
   ```

2. **Find "Connection pooling" section**

3. **Select "Transaction" mode**

4. **Copy the connection string** (looks like):
   ```
   postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   ```
   → This goes in `DATABASE_URL`

   **Important notes:**
   - Use port **6543** (connection pooling), not 5432 (direct connection)
   - Use "Transaction" mode for best compatibility
   - You'll need your database password (set when you created the project)

### Step 4: Update .env File

Edit your `.env` file and replace the local URLs with the cloud URLs:

```bash
# Before (local - WRONG for production):
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=eyJ...local...
SUPABASE_SERVICE_KEY=eyJ...local...
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/iswitch_crm

# After (cloud - CORRECT for production):
SUPABASE_URL=https://tdwpzktihdeuza.supabase.co  # Your actual project URL
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Your actual anon key
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Your actual service role key
DATABASE_URL=postgresql://postgres.tdwpzktihdeuza:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

### Step 5: Verify Your Supabase Project Exists

If you haven't created a Supabase project yet, you need to:

1. **Create a new project:**
   - Go to: https://supabase.com/dashboard
   - Click "New Project"
   - Name: `iswitch-crm`
   - Database Password: Choose a strong password (save it!)
   - Region: Choose closest to your users
   - Click "Create new project" (takes 2-3 minutes)

2. **Run database migrations:**
   Once the project is created, you'll need to set up your database schema:
   - Tables: leads, customers, projects, etc.
   - Policies: Row-level security settings
   - Functions: Any stored procedures

## Quick Check

Run this to see what you currently have:

```bash
grep -E "^(DATABASE_URL|SUPABASE_URL)" .env
```

You should see **cloud URLs** (https://... and aws-...), not local URLs (127.0.0.1).

## Troubleshooting

### I don't have a Supabase cloud project

**Solution:** Create one at https://supabase.com/dashboard

- Free tier available
- Takes 2-3 minutes to provision
- Save your database password!

### I forgot my database password

**Solution:** Reset it in Supabase dashboard:
1. Settings → Database
2. "Reset database password"
3. Update DATABASE_URL with new password

### My Supabase project is empty (no tables)

**Solution:** You need to migrate your local database schema to cloud:

1. Export local schema:
   ```bash
   pg_dump -h 127.0.0.1 -U postgres -d iswitch_crm --schema-only > schema.sql
   ```

2. Import to Supabase via SQL Editor in dashboard

OR use Supabase CLI to sync:
```bash
supabase link --project-ref [your-project-ref]
supabase db push
```

## Next Steps

Once you have updated `.env` with cloud Supabase URLs:

1. Verify the URLs:
   ```bash
   grep -E "^(DATABASE_URL|SUPABASE_URL)" .env
   ```

2. Run the deployment script:
   ```bash
   ./set-render-env-vars.sh
   ```

3. The script will:
   - Verify you have cloud URLs
   - Set environment variables in Render
   - Trigger deployment
   - Monitor until healthy
   - Tell you next steps

---

**Key Point:** Local development URLs (127.0.0.1) won't work for Render deployment. You must use Supabase cloud URLs.
