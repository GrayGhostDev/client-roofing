# Frequently Asked Questions (FAQ)

Common questions and answers about the iSwitch Roofs CRM system.

## Table of Contents
- [General](#general)
- [Access & Login](#access--login)
- [Customers & Leads](#customers--leads)
- [Projects](#projects)
- [Appointments](#appointments)
- [Technical Issues](#technical-issues)
- [Data & Reports](#data--reports)

---

## General

### What is the iSwitch Roofs CRM?
The iSwitch Roofs CRM is a comprehensive customer relationship management system designed specifically for roofing companies. It helps manage customers, leads, projects, appointments, and communications in one central platform.

### What browsers are supported?
- **Recommended:** Chrome 90+ or Firefox 88+
- **Supported:** Safari 14+, Edge 90+
- **Mobile:** iOS Safari 14+, Android Chrome 90+

### Is the system mobile-friendly?
Yes! The entire system is responsive and works on smartphones and tablets. You can access all features on mobile devices, though some admin functions work best on desktop.

### Where is my data stored?
All data is securely stored in Supabase PostgreSQL database with encryption at rest. Backups are performed daily with 30-day retention. Data is hosted in US data centers.

### Is my data secure?
Yes. We use:
- TLS 1.3 encryption for data in transit
- Database encryption at rest
- JWT authentication with bcrypt password hashing
- Role-based access control (RBAC)
- Regular security audits

---

## Access & Login

### How do I login for the first time?
1. Go to `https://app.iswitchroofs.com`
2. Enter the email address provided by your administrator
3. Enter the temporary password (provided separately)
4. You'll be prompted to create a new password
5. Set a strong password (min 8 characters, includes uppercase, lowercase, number)
6. Click "Update Password"

### I forgot my password. How do I reset it?
1. Click "Forgot Password?" on the login page
2. Enter your email address
3. Check your email for reset link (arrives within 5 minutes)
4. Click the link in the email
5. Enter your new password
6. Confirm new password
7. Click "Reset Password"

**Note:** Reset links expire after 1 hour for security.

### Why can't I login?
Common reasons:
- **Incorrect password** - Try password reset
- **Account deactivated** - Contact your administrator
- **Browser cookies disabled** - Enable cookies
- **Wrong email address** - Check with administrator
- **Caps Lock on** - Passwords are case-sensitive

### How long does my session last?
Sessions last 24 hours by default. After 24 hours of inactivity, you'll need to login again. You can enable "Remember me" to extend sessions to 30 days.

### Can I use the same login on multiple devices?
Yes! You can login from multiple devices simultaneously. Your session syncs across all devices in real-time.

---

## Customers & Leads

### What's the difference between a customer and a lead?
- **Lead:** A potential customer who has shown interest but hasn't signed a contract yet
- **Customer:** An actual customer with whom you have (or had) a business relationship

A lead becomes a customer when they sign a contract or agree to work with you.

### How do I create a new customer?
1. Click "Customers" in sidebar
2. Click "+ Add Customer" button
3. Fill in required fields (name, email)
4. Add optional information (phone, address, segment)
5. Click "Save Customer"

### Can I have duplicate customer emails?
No. Email addresses must be unique in the system. If you try to create a customer with an existing email, you'll see an error message. This prevents duplicate customer records.

### How is lead score calculated?
Lead score (0-100) is automatically calculated based on:
- **Project value** (40 points max) - Higher value = more points
- **Urgency** (30 points max) - Immediate need = more points
- **Source quality** (20 points max) - Referrals score highest
- **Customer segment** (10 points max) - Premium customers score higher

### Can I manually change a lead score?
No. Lead scores are calculated automatically to ensure consistency. However, you can set lead priority (High, Medium, Low) manually to override automatic scoring for special cases.

### How do I convert a lead to a customer?
1. Open the lead details
2. Click "Convert to Project" button
3. Fill in project details
4. Click "Create Project"
5. Lead status automatically changes to "Converted"
6. New project is created and linked to customer

### What happens to lost leads?
Lost leads remain in the system with status "Lost". You can:
- Re-open them later if customer returns
- View lost lead reports to analyze why leads were lost
- Archive them after 6 months (automatic)

---

## Projects

### How do I create a new project?
1. Navigate to "Projects"
2. Click "+ Add Project"
3. Select customer (required)
4. Enter project name, type, and budget
5. Set start and end dates
6. Assign team members
7. Click "Create Project"

### Can a project have multiple team members?
Yes! You can assign multiple team members to a project. All assigned members will:
- See the project in their task list
- Receive project notifications
- Be able to update project progress

### How do I track project progress?
1. Open project details
2. Click "Update Progress"
3. Enter completion percentage (0-100%)
4. Update actual cost (running total)
5. Add notes about what was completed
6. Upload photos (optional)
7. Click "Save Progress"

**Best Practice:** Update progress at least weekly.

### What if a project goes on hold?
1. Open project details
2. Click "Change Status"
3. Select "On Hold"
4. Enter reason for hold
5. Add estimated resume date (optional)
6. Click "Save"

Customer will receive notification if enabled.

### Can I delete a project?
Only administrators can delete projects. If you need a project removed, contact your administrator. Typically, projects should be marked "Cancelled" rather than deleted to preserve history.

### What happens when a project is completed?
1. Update completion percentage to 100%
2. Change status to "Completed"
3. System records completion date
4. Final invoice can be generated (if configured)
5. Customer receives completion notification (if enabled)
6. Project moves to "Completed" list

---

## Appointments

### How do I schedule an appointment?
1. Navigate to "Appointments"
2. Click "+ Schedule Appointment"
3. Select customer and project (if applicable)
4. Choose appointment type (Inspection, Consultation, etc.)
5. Set date, time, and duration
6. Assign team member
7. Enter location (auto-filled from customer address)
8. Enable reminders (recommended)
9. Click "Create Appointment"

### Can I schedule recurring appointments?
Not currently. Each appointment must be scheduled individually. Recurring appointments are planned for a future release.

### How do I reschedule an appointment?
**Method 1 - Drag & Drop:**
1. Go to calendar view
2. Drag appointment to new date/time
3. Confirm reschedule
4. System sends notification

**Method 2 - Edit:**
1. Click on appointment
2. Click "Edit"
3. Change date/time
4. Click "Save Changes"

### What if a customer doesn't show up?
1. Find the appointment
2. Click "Mark as No-Show"
3. Add notes about attempted contact
4. System logs no-show
5. Consider follow-up call

### Do customers receive appointment reminders?
Yes, if enabled when creating the appointment:
- **Email reminder:** Sent 24 hours before
- **SMS reminder:** Sent 2 hours before (if SMS configured)

Team members also receive reminder 30 minutes before.

### Can I see all team appointments?
- **Managers & Admins:** See all team appointments
- **Sales & Field Techs:** See only their own appointments

Use calendar filters to view specific team members' schedules.

---

## Technical Issues

### The system is loading slowly. What should I do?
**Quick fixes:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Close unused browser tabs
3. Check internet connection speed
4. Try different browser

**If problem persists:**
- Contact support: support@iswitchroofs.com
- Include: Browser version, internet speed, specific slow pages

### I'm getting "Session expired" messages frequently
**Cause:** Your session timeout is set to 24 hours by default.

**Solutions:**
- Enable "Remember me" on login (extends to 30 days)
- Check if browser is clearing cookies
- Contact admin if issue persists

### Changes I make aren't saving
**Check:**
1. Do you have permission to make this change?
2. Are all required fields filled?
3. Is your internet connection stable?
4. Try refreshing the page

**If problem continues:**
- Log out and log back in
- Clear browser cache
- Contact support with specific details

### I can't upload files/photos
**Requirements:**
- Maximum file size: 10MB
- Supported formats: JPG, PNG, PDF, DOCX
- Stable internet connection required

**Troubleshooting:**
1. Check file size (< 10MB)
2. Check file format
3. Try different browser
4. Disable browser extensions temporarily

### Error message: "Something went wrong"
This is a general error message. **Steps:**
1. Refresh the page (F5)
2. Log out and log back in
3. Try same action again
4. If persists, screenshot error and contact support

---

## Data & Reports

### Can I export customer data?
Yes! (Admin & Manager roles only)
1. Navigate to Customers
2. Click "Export" button
3. Select export format (CSV, Excel, JSON)
4. Apply filters if needed
5. Click "Download"

### How do I generate a report?
(Manager & Admin roles only)
1. Navigate to Analytics
2. Select report type
3. Configure date range and filters
4. Click "Generate Report"
5. View online or export to PDF/Excel

### Can I import customers from a spreadsheet?
Yes! (Admin only)
1. Prepare CSV/Excel file with required columns
2. Navigate to Admin → Data Management → Import
3. Select "Customer Import"
4. Upload file
5. Map columns
6. Review validation results
7. Confirm import

See [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for detailed import instructions.

### How far back does data history go?
- **Customers, Leads, Projects:** Retained indefinitely
- **Interactions:** Retained indefinitely
- **Audit Logs:** 90 days (then archived)
- **Analytics Snapshots:** 24 months

### Can I recover deleted data?
Depends on what was deleted:
- **Customers/Projects:** Soft deleted, can be recovered within 30 days
- **Appointments:** Cancelled appointments retained for 12 months
- **Users:** Contact administrator for recovery

**Note:** Only administrators can recover deleted data.

### How accurate are the analytics?
Analytics are calculated in real-time from your data:
- **Revenue:** Actual project costs recorded
- **Conversion rates:** Based on lead status changes
- **Response times:** Logged interaction timestamps

Data accuracy depends on:
✓ Timely status updates
✓ Accurate cost tracking
✓ Logging all interactions
✓ Correct date entries

---

## Still Have Questions?

### Contact Support
- **Email:** support@iswitchroofs.com
- **Phone:** 1-800-XXX-XXXX
- **Hours:** Monday-Friday, 9 AM - 5 PM EST
- **Response Time:** Within 24 hours (usually faster)

### Additional Resources
- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
- **Admin Guide:** [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
- **Video Tutorials:** app.iswitchroofs.com/training
- **API Documentation:** [API_REFERENCE.md](API_REFERENCE.md)

### Feature Requests
Have an idea for improvement? Submit feature requests to: features@iswitchroofs.com

Include:
- Description of feature
- Problem it solves
- How you'd use it

We review all submissions and prioritize based on user feedback!
