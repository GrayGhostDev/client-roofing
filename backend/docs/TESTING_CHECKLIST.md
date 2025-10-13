# Manual Testing Checklist - Real-Time Synchronization

## Overview
This checklist covers manual testing of real-time synchronization features across the iSwitch Roofs CRM dashboard. Tests verify that changes in one browser tab/window are immediately reflected in all other open tabs via Pusher WebSocket connections.

**Estimated Time**: 30 minutes
**Required Browser**: Chrome/Edge (with DevTools)
**Required Accounts**: 1 test user account
**Prerequisites**: Backend running on http://localhost:8000, Streamlit dashboard on http://localhost:8501

---

## Setup Instructions (5 minutes)

### Browser Configuration

1. **Open 3 Browser Tabs**:
   - Tab 1: Lead Management (`http://localhost:8501/Lead_Management`)
   - Tab 2: Dashboard/Home (`http://localhost:8501`)
   - Tab 3: Customer Management (`http://localhost:8501/Customer_Management`)

2. **Enable DevTools in All Tabs**:
   - Press `F12` or `Cmd+Option+I` (Mac)
   - Navigate to **Network** tab
   - Filter by "pusher" to see WebSocket events

3. **Open Pusher Debug Console** (Optional):
   - Visit: https://dashboard.pusher.com/apps/YOUR_APP_ID/getting_started
   - Click "Debug Console" tab
   - Keep this open to monitor all events

### Verification Checklist

- [ ] All 3 tabs loaded successfully
- [ ] DevTools Network tab open in all tabs
- [ ] Pusher WebSocket connection established (check for "ws://" connections)
- [ ] No console errors in any tab

---

## Test Scenario 1: Lead Creation Sync (5 minutes)

**Objective**: Verify that creating a lead in one tab updates the dashboard immediately.

### Steps

1. **In Tab 1 (Lead Management)**:
   - [ ] Click "Create New Lead" button
   - [ ] Fill in form:
     - First Name: "John"
     - Last Name: "Sync Test"
     - Email: "john.synctest@example.com"
     - Phone: "248-555-0001"
     - Source: "Google LSA"
     - City: "Birmingham"
     - Status: "New"
   - [ ] Click "Save"

2. **Verify Tab 1 (Lead Management)**:
   - [ ] Success toast notification appears (green, top-right)
   - [ ] New lead appears in leads table
   - [ ] Lead status shows "New"
   - [ ] Lead score is calculated (should be 70-85)

3. **Verify Tab 2 (Dashboard)**:
   - [ ] Dashboard refreshes within 2 seconds (automatic)
   - [ ] "Total Leads" count incremented by 1
   - [ ] "New Leads" count incremented by 1
   - [ ] Toast notification: "New lead added: John Sync Test"

4. **Verify DevTools Network**:
   - [ ] In Tab 1: See POST request to `/api/leads`
   - [ ] In Tab 1: See Pusher event: `pusher:connection_established`
   - [ ] In Tab 2: See Pusher event: `lead-created` on `crm-leads-channel`
   - [ ] Event payload contains lead ID, name, status

5. **Check Pusher Debug Console** (if open):
   - [ ] Event shows channel: `crm-leads-channel`
   - [ ] Event name: `lead-created`
   - [ ] Timestamp matches creation time

### Expected Results
- ✅ Lead created successfully in Tab 1
- ✅ Dashboard (Tab 2) updates within 2 seconds
- ✅ Pusher event visible in DevTools
- ✅ No errors in console

### Screenshots
- [ ] Screenshot of Tab 1 after creation (with success toast)
- [ ] Screenshot of Tab 2 showing updated metrics
- [ ] Screenshot of DevTools showing Pusher event

---

## Test Scenario 2: Customer Conversion Sync (5 minutes)

**Objective**: Verify that converting a lead to customer updates both Leads and Customers pages.

### Steps

1. **In Tab 1 (Lead Management)**:
   - [ ] Select the lead created in Scenario 1
   - [ ] Click "Convert to Customer" button
   - [ ] Confirm conversion in modal dialog
   - [ ] Wait for success message

2. **Verify Tab 1 (Lead Management)**:
   - [ ] Lead status changes to "Converted"
   - [ ] Lead row background changes color (usually gray/muted)
   - [ ] Toast: "Lead converted to customer successfully"

3. **Verify Tab 3 (Customer Management)**:
   - [ ] Customer table refreshes automatically
   - [ ] New customer "John Sync Test" appears
   - [ ] Customer status: "Active"
   - [ ] Toast: "New customer added: John Sync Test"

4. **Verify Tab 2 (Dashboard)**:
   - [ ] "Total Customers" count incremented by 1
   - [ ] "Converted Leads" count incremented by 1
   - [ ] Conversion rate percentage updated

5. **Verify DevTools Network**:
   - [ ] In Tab 1: POST to `/api/customers`
   - [ ] In Tab 1: PUT to `/api/leads/{id}` (status update)
   - [ ] In Tab 3: Pusher event `customer-created`
   - [ ] In Tab 1: Pusher event `lead-updated`

### Expected Results
- ✅ Lead converted successfully
- ✅ Customer appears in Tab 3 within 2 seconds
- ✅ Dashboard metrics updated
- ✅ Two Pusher events fired: `lead-updated` and `customer-created`

### Screenshots
- [ ] Screenshot showing lead status "Converted"
- [ ] Screenshot of new customer in Customer Management
- [ ] Screenshot of Dashboard with updated conversion metrics

---

## Test Scenario 3: Project Status Update Sync (5 minutes)

**Objective**: Verify that project status changes update the dashboard revenue metrics in real-time.

### Steps

1. **Setup**:
   - [ ] Ensure at least 1 project exists in the system
   - [ ] Navigate to Projects page in a new tab (Tab 4)

2. **In Tab 4 (Projects)**:
   - [ ] Select an "In Progress" project
   - [ ] Change status to "Completed"
   - [ ] Enter completion date: Today
   - [ ] Enter final cost: $28,500
   - [ ] Click "Save"

3. **Verify Tab 4 (Projects)**:
   - [ ] Project status updated to "Completed"
   - [ ] Completion badge/icon appears
   - [ ] Toast: "Project completed successfully"

4. **Verify Tab 2 (Dashboard)**:
   - [ ] "Active Projects" count decremented by 1
   - [ ] "Completed Projects" count incremented by 1
   - [ ] "Total Revenue" increased by $28,500
   - [ ] Revenue chart updates (if visible)

5. **Verify DevTools**:
   - [ ] PUT request to `/api/projects/{id}`
   - [ ] Pusher event: `project-updated` on `crm-projects-channel`
   - [ ] Event payload contains: status, completion_date, final_cost

### Expected Results
- ✅ Project status updated successfully
- ✅ Dashboard revenue metrics updated within 2 seconds
- ✅ Pusher event delivered to all tabs
- ✅ No calculation errors in revenue totals

---

## Test Scenario 4: Multi-Tab Concurrent Edits (5 minutes)

**Objective**: Verify that concurrent edits from multiple tabs are handled correctly without data loss.

### Steps

1. **Setup**:
   - [ ] Open Lead Management in Tab 1 and Tab 5 (duplicate tab)
   - [ ] Select the same lead in both tabs

2. **In Tab 1**:
   - [ ] Click "Edit" on lead
   - [ ] Change status to "Qualified"
   - [ ] Do NOT save yet

3. **In Tab 5**:
   - [ ] Click "Edit" on the same lead
   - [ ] Change temperature to "Hot"
   - [ ] Click "Save"

4. **In Tab 1**:
   - [ ] Click "Save" (attempting to save first edit)

5. **Verify Expected Behavior**:
   - [ ] Tab 1 shows warning: "This record was modified by another user"
   - [ ] Tab 1 offers options: "Reload" or "Override"
   - [ ] If "Reload" clicked: Tab 1 shows updated data from Tab 5
   - [ ] If "Override" clicked: Tab 1 changes overwrite Tab 5 changes (last-write-wins)

6. **Alternative Test** (if no conflict detection):
   - [ ] Second save (Tab 1) succeeds
   - [ ] Both tabs receive Pusher `lead-updated` event
   - [ ] Both tabs refresh to show latest state
   - [ ] Last save (Tab 1) is persisted

### Expected Results
- ✅ Conflict detected or last-write-wins behavior confirmed
- ✅ No data corruption
- ✅ Both tabs show consistent final state
- ✅ Pusher events delivered to both tabs

---

## Test Scenario 5: Cache Performance Verification (5 minutes)

**Objective**: Verify that Redis caching improves load times and cache hit rate is >80%.

### Steps

1. **Clear Browser Cache**:
   - [ ] Open DevTools → Application → Clear Storage
   - [ ] Click "Clear site data"

2. **Clear Redis Cache** (via API):
   ```bash
   curl -X POST http://localhost:8000/api/cache/clear
   ```
   - [ ] Verify response: `{"success": true, "keys_deleted": N}`

3. **First Dashboard Load (Cache Miss)**:
   - [ ] Reload Tab 2 (Dashboard)
   - [ ] In DevTools → Network, record load time for `/api/analytics/dashboard`
   - [ ] Expected: 800ms - 1200ms (no cache)

4. **Second Dashboard Load (Cache Hit)**:
   - [ ] Wait 2 seconds
   - [ ] Reload Tab 2 again
   - [ ] Record load time for `/api/analytics/dashboard`
   - [ ] Expected: 150ms - 350ms (with cache)

5. **Check Cache Stats**:
   ```bash
   curl http://localhost:8000/api/cache/stats
   ```
   - [ ] Verify `hit_rate_percent` > 80%
   - [ ] Verify `total_requests` > 0
   - [ ] Verify `hits` > `misses`

6. **Verify Cache Invalidation**:
   - [ ] Create a new lead (Tab 1)
   - [ ] Reload Dashboard (Tab 2)
   - [ ] Verify load time increases slightly (cache was invalidated)
   - [ ] Check cache stats again: verify `misses` incremented

### Expected Results
- ✅ First load: 800-1200ms (cache miss)
- ✅ Second load: 150-350ms (cache hit) - **70-80% faster**
- ✅ Cache hit rate >80% after multiple requests
- ✅ Cache invalidated on data changes

### Performance Benchmarks
| Metric | Target | Status |
|--------|--------|--------|
| Dashboard load (cached) | <350ms | [ ] Pass / [ ] Fail |
| Dashboard load (uncached) | <1200ms | [ ] Pass / [ ] Fail |
| Cache hit rate | >80% | [ ] Pass / [ ] Fail |
| Pusher event delivery | <500ms | [ ] Pass / [ ] Fail |

---

## Troubleshooting Guide

### Issue: Pusher Events Not Received

**Symptoms**: Dashboard doesn't update when changes made in another tab

**Checks**:
1. [ ] Verify Pusher credentials in `.env`:
   ```
   PUSHER_APP_ID=your_app_id
   PUSHER_KEY=your_key
   PUSHER_SECRET=your_secret
   PUSHER_CLUSTER=us2
   ```
2. [ ] Check backend logs for Pusher connection errors
3. [ ] Verify WebSocket connection in DevTools → Network → WS
4. [ ] Check Pusher Dashboard for connection count

**Solution**: Restart backend with correct Pusher credentials

---

### Issue: Slow Dashboard Load Times

**Symptoms**: Dashboard loads taking >2 seconds consistently

**Checks**:
1. [ ] Check Redis connection: `redis-cli ping` → should return "PONG"
2. [ ] Check cache stats: `curl http://localhost:8000/api/cache/stats`
3. [ ] Verify database connection pool not exhausted
4. [ ] Check backend logs for query slowness

**Solution**:
- Restart Redis: `redis-server`
- Run database indexes: `backend/migrations/003_performance_indexes.sql`
- Clear and warm cache: `python scripts/warm_cache.py`

---

### Issue: Concurrent Edit Conflicts

**Symptoms**: Data loss or unexpected overwrites when editing from multiple tabs

**Checks**:
1. [ ] Verify `updated_at` timestamp in database
2. [ ] Check if optimistic locking is enabled
3. [ ] Review audit logs for edit sequence

**Solution**: Implement optimistic locking or add version numbers to entities

---

## Test Results Summary

### Overall Results
- [ ] All scenarios passed
- [ ] Some scenarios failed (list below)
- [ ] Performance targets met

### Failed Scenarios (if any)
1. Scenario #: _______________
   - Issue: _______________
   - Root cause: _______________
   - Action needed: _______________

### Performance Summary
| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Cache hit rate | >80% | ___% | [ ] Pass / [ ] Fail |
| Dashboard load (cached) | <350ms | ___ms | [ ] Pass / [ ] Fail |
| Pusher event delivery | <500ms | ___ms | [ ] Pass / [ ] Fail |
| Concurrent users supported | 60+ | ___ | [ ] Pass / [ ] Fail |

### Recommendations
1. _______________
2. _______________
3. _______________

---

## Sign-Off

**Tester**: _______________
**Date**: _______________
**Environment**: [ ] Local [ ] Staging [ ] Production
**Overall Assessment**: [ ] Ready for production [ ] Needs fixes [ ] Blocked

**Additional Notes**:
_______________________________________________
_______________________________________________
_______________________________________________
