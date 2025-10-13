"""
Locust Load Testing Suite for iSwitch Roofs CRM
Simulates realistic user behavior patterns with 100 concurrent users

User Types:
- DashboardUser (40%): Views dashboard and metrics
- LeadManagementUser (30%): CRUD operations on leads
- ProjectViewUser (20%): Views and filters projects
- AnalyticsUser (10%): Heavy analytics queries

Performance Targets:
- 95th percentile response time: <500ms
- Error rate: <1%
- Throughput: >500 requests/second
- Cache hit rate: >80%

Usage:
    # Install Locust
    pip install locust==2.15.1

    # Run load test
    locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --html report.html

    # Monitor during test:
    # - http://localhost:8089 (Locust Web UI)
    # - http://localhost:8000/api/cache/stats (Cache stats)
    # - Backend logs for errors
"""

import random
import json
from datetime import datetime, timedelta
from locust import HttpUser, task, between, tag, events


# Test data generators
def generate_lead_data():
    """Generate realistic lead data for creation."""
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis"]
    sources = ["Google LSA", "Facebook Ads", "Website", "Referral", "Insurance Agent"]
    cities = ["Birmingham", "Bloomfield Hills", "Troy", "Rochester Hills"]

    return {
        "first_name": random.choice(first_names),
        "last_name": random.choice(last_names),
        "email": f"test.{random.randint(1000, 9999)}@loadtest.com",
        "phone": f"248-555-{random.randint(1000, 9999)}",
        "source": random.choice(sources),
        "city": random.choice(cities),
        "state": "MI",
        "zip_code": "48009",
        "status": "new"
    }


def generate_customer_data():
    """Generate realistic customer data."""
    first_names = ["Robert", "Mary", "James", "Patricia", "William"]
    last_names = ["Miller", "Wilson", "Moore", "Taylor", "Anderson"]

    return {
        "first_name": random.choice(first_names),
        "last_name": random.choice(last_names),
        "email": f"customer.{random.randint(1000, 9999)}@loadtest.com",
        "phone": f"248-555-{random.randint(1000, 9999)}",
        "city": random.choice(["Birmingham", "Troy", "Rochester Hills"]),
        "state": "MI"
    }


# Cache hit rate tracking
cache_hits = 0
cache_misses = 0


@events.request.add_listener
def track_cache_performance(request_type, name, response_time, response_length, exception, **kwargs):
    """Track cache performance during load test."""
    global cache_hits, cache_misses

    # Check response headers for cache indicators
    # (Assume backend adds X-Cache-Hit header)
    if hasattr(kwargs.get('context'), 'headers'):
        if kwargs['context'].headers.get('X-Cache-Hit') == 'true':
            cache_hits += 1
        else:
            cache_misses += 1


@events.test_stop.add_listener
def print_cache_stats(environment, **kwargs):
    """Print cache statistics at end of test."""
    global cache_hits, cache_misses
    total = cache_hits + cache_misses

    if total > 0:
        hit_rate = (cache_hits / total) * 100
        print("\n" + "="*60)
        print("CACHE PERFORMANCE STATISTICS")
        print("="*60)
        print(f"Cache Hits: {cache_hits}")
        print(f"Cache Misses: {cache_misses}")
        print(f"Hit Rate: {hit_rate:.2f}%")
        print(f"Target: >80%")
        print(f"Status: {'✅ PASS' if hit_rate >= 80 else '❌ FAIL'}")
        print("="*60)


class DashboardUser(HttpUser):
    """
    Simulates users primarily viewing dashboard and metrics.
    Weight: 40% - Represents most common use case (management/overview)
    """
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    weight = 40  # 40% of total users

    def on_start(self):
        """Initialize user session (runs once per user)."""
        # Simulate login (if authentication required)
        # self.client.post("/api/auth/login", json={"username": "testuser", "password": "password"})
        pass

    @task(5)
    @tag('dashboard', 'read')
    def view_dashboard(self):
        """View main dashboard metrics (most common action)."""
        with self.client.get("/api/analytics/dashboard", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard load failed: {response.status_code}")

    @task(3)
    @tag('metrics', 'read')
    def view_business_metrics(self):
        """View business metrics summary."""
        self.client.get("/api/business-metrics/summary")

    @task(2)
    @tag('cache', 'read')
    def check_cache_stats(self):
        """Check cache statistics (monitoring)."""
        self.client.get("/api/cache/stats")

    @task(1)
    @tag('analytics', 'read')
    def view_recent_activity(self):
        """View recent activity feed."""
        self.client.get("/api/analytics/recent-activity?limit=20")


class LeadManagementUser(HttpUser):
    """
    Simulates users managing leads (CRUD operations).
    Weight: 30% - Sales team actively working leads
    """
    wait_time = between(1, 3)
    weight = 30

    lead_ids = []  # Store created lead IDs for updates/deletes

    @task(10)
    @tag('leads', 'read')
    def list_leads(self):
        """List leads with pagination (most frequent operation)."""
        page = random.randint(1, 5)
        per_page = random.choice([25, 50, 100])
        status = random.choice(['new', 'contacted', 'qualified', 'converted', None])

        params = f"?page={page}&per_page={per_page}"
        if status:
            params += f"&status={status}"

        self.client.get(f"/api/leads{params}")

    @task(3)
    @tag('leads', 'write')
    def create_lead(self):
        """Create a new lead."""
        lead_data = generate_lead_data()

        with self.client.post("/api/leads", json=lead_data, catch_response=True) as response:
            if response.status_code == 201:
                try:
                    lead = response.json()
                    if 'id' in lead:
                        self.lead_ids.append(lead['id'])
                    response.success()
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Lead creation failed: {response.status_code}")

    @task(5)
    @tag('leads', 'read')
    def view_lead_details(self):
        """View individual lead details."""
        if self.lead_ids:
            lead_id = random.choice(self.lead_ids)
            self.client.get(f"/api/leads/{lead_id}")
        else:
            # Fallback: list leads and pick one
            response = self.client.get("/api/leads?per_page=10")
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('data'):
                        lead = random.choice(data['data'])
                        self.lead_ids.append(lead['id'])
                except:
                    pass

    @task(4)
    @tag('leads', 'write')
    def update_lead_status(self):
        """Update lead status (common workflow action)."""
        if self.lead_ids:
            lead_id = random.choice(self.lead_ids)
            new_status = random.choice(['contacted', 'qualified', 'proposal_sent'])

            update_data = {
                "status": new_status,
                "notes": f"Updated by load test at {datetime.utcnow().isoformat()}"
            }

            self.client.put(f"/api/leads/{lead_id}", json=update_data)

    @task(2)
    @tag('leads', 'read')
    def search_leads(self):
        """Search leads by various criteria."""
        search_terms = ["roof", "insurance", "Birmingham", "urgent", "John"]
        term = random.choice(search_terms)

        self.client.get(f"/api/leads/search?q={term}")

    @task(1)
    @tag('leads', 'write')
    def delete_lead(self):
        """Delete a lead (least common operation)."""
        if len(self.lead_ids) > 5:  # Only delete if we have multiple
            lead_id = self.lead_ids.pop()
            self.client.delete(f"/api/leads/{lead_id}")


class ProjectViewUser(HttpUser):
    """
    Simulates users viewing and filtering projects.
    Weight: 20% - Project managers and executives
    """
    wait_time = between(2, 4)
    weight = 20

    @task(6)
    @tag('projects', 'read')
    def list_projects(self):
        """List projects with various filters."""
        page = random.randint(1, 3)
        status = random.choice(['in_progress', 'completed', 'approved', None])

        params = f"?page={page}&per_page=50"
        if status:
            params += f"&status={status}"

        self.client.get(f"/api/projects{params}")

    @task(3)
    @tag('projects', 'read')
    def view_project_details(self):
        """View individual project details."""
        # Get recent projects first
        response = self.client.get("/api/projects?per_page=10")
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('data'):
                    project = random.choice(data['data'])
                    self.client.get(f"/api/projects/{project['id']}")
            except:
                pass

    @task(2)
    @tag('projects', 'read')
    def filter_projects_by_value(self):
        """Filter projects by value range."""
        min_value = random.choice([10000, 20000, 30000])
        max_value = min_value + random.choice([20000, 30000, 40000])

        self.client.get(f"/api/projects?min_value={min_value}&max_value={max_value}")

    @task(2)
    @tag('analytics', 'read')
    def view_project_analytics(self):
        """View project performance analytics."""
        self.client.get("/api/analytics/projects-summary")

    @task(1)
    @tag('customers', 'read')
    def view_customer_projects(self):
        """View projects for a specific customer."""
        # Get customers first
        response = self.client.get("/api/customers?per_page=10")
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('data'):
                    customer = random.choice(data['data'])
                    self.client.get(f"/api/customers/{customer['id']}/projects")
            except:
                pass


class AnalyticsUser(HttpUser):
    """
    Simulates users running heavy analytics queries.
    Weight: 10% - Executives and analysts
    """
    wait_time = between(3, 6)  # Longer waits (reviewing data)
    weight = 10

    @task(4)
    @tag('analytics', 'read', 'heavy')
    def view_conversion_funnel(self):
        """View conversion funnel (expensive query)."""
        days = random.choice([30, 60, 90])
        self.client.get(f"/api/enhanced-analytics/conversion-funnel?days={days}")

    @task(3)
    @tag('analytics', 'read', 'heavy')
    def view_revenue_trends(self):
        """View revenue trends over time."""
        period = random.choice(['daily', 'weekly', 'monthly'])
        self.client.get(f"/api/analytics/revenue-trends?period={period}")

    @task(3)
    @tag('analytics', 'read', 'heavy')
    def view_lead_source_performance(self):
        """Analyze lead source ROI."""
        self.client.get("/api/enhanced-analytics/lead-source-performance")

    @task(2)
    @tag('analytics', 'read')
    def view_team_performance(self):
        """View team member performance metrics."""
        self.client.get("/api/analytics/team-performance")

    @task(2)
    @tag('analytics', 'read', 'heavy')
    def view_geographic_analysis(self):
        """Analyze performance by geography."""
        self.client.get("/api/enhanced-analytics/geographic-heatmap")

    @task(1)
    @tag('analytics', 'read', 'heavy')
    def generate_custom_report(self):
        """Generate custom analytics report."""
        report_params = {
            "start_date": (datetime.utcnow() - timedelta(days=90)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "metrics": ["leads", "conversions", "revenue"],
            "group_by": random.choice(["source", "city", "status"])
        }

        self.client.post("/api/analytics/custom-report", json=report_params)


class WebSocketConnectionUser(HttpUser):
    """
    Simulates users maintaining WebSocket connections for real-time updates.
    Weight: 5% - Background connections for all active users
    """
    wait_time = between(10, 20)  # Long-lived connections
    weight = 5

    @task(1)
    @tag('realtime', 'websocket')
    def maintain_pusher_connection(self):
        """Simulate maintaining Pusher WebSocket connection."""
        # In a real scenario, this would establish and maintain a WebSocket
        # For HTTP load testing, we simulate periodic polling
        self.client.get("/api/realtime/ping")

    @task(2)
    @tag('realtime', 'read')
    def check_realtime_status(self):
        """Check real-time connection status."""
        self.client.get("/api/realtime/status")


# Custom user class for mixed workload
class MixedWorkloadUser(HttpUser):
    """
    User that performs a mix of operations (realistic usage pattern).
    Combines reading, writing, and analytics in typical workflow.
    """
    wait_time = between(1, 4)
    weight = 15  # 15% of users have mixed behavior

    @task(3)
    def typical_morning_routine(self):
        """Simulates typical morning workflow: check dashboard, view leads, update statuses."""
        # 1. Check dashboard
        self.client.get("/api/analytics/dashboard")

        # 2. View new leads
        self.client.get("/api/leads?status=new&per_page=20")

        # 3. Update a lead
        lead_data = generate_lead_data()
        response = self.client.post("/api/leads", json=lead_data)

        if response.status_code == 201:
            try:
                lead = response.json()
                # Update it immediately
                self.client.put(f"/api/leads/{lead['id']}", json={"status": "contacted"})
            except:
                pass

    @task(2)
    def project_review_workflow(self):
        """Simulates project review workflow."""
        # 1. View active projects
        self.client.get("/api/projects?status=in_progress")

        # 2. Check project analytics
        self.client.get("/api/analytics/projects-summary")

        # 3. View recent interactions
        self.client.get("/api/interactions?recent=true&limit=10")

    @task(1)
    def create_full_lead_workflow(self):
        """Simulates complete lead creation and follow-up workflow."""
        # 1. Create lead
        lead_data = generate_lead_data()
        response = self.client.post("/api/leads", json=lead_data)

        if response.status_code == 201:
            try:
                lead = response.json()
                lead_id = lead['id']

                # 2. Create interaction
                interaction_data = {
                    "entity_type": "lead",
                    "entity_id": lead_id,
                    "interaction_type": "call",
                    "subject": "Initial contact",
                    "content": "Discussed roofing needs"
                }
                self.client.post("/api/interactions", json=interaction_data)

                # 3. Schedule appointment
                appointment_data = {
                    "entity_type": "lead",
                    "entity_id": lead_id,
                    "title": "Initial consultation",
                    "scheduled_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                    "duration_minutes": 60
                }
                self.client.post("/api/appointments", json=appointment_data)
            except:
                pass


# Performance thresholds for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test configuration on start."""
    print("\n" + "="*60)
    print("LOCUST LOAD TEST STARTED")
    print("="*60)
    print(f"Target Host: {environment.host}")
    print(f"User Distribution:")
    print(f"  - DashboardUser: 40%")
    print(f"  - LeadManagementUser: 30%")
    print(f"  - ProjectViewUser: 20%")
    print(f"  - AnalyticsUser: 10%")
    print(f"  - MixedWorkloadUser: 15%")
    print(f"\nPerformance Targets:")
    print(f"  - 95th percentile: <500ms")
    print(f"  - Error rate: <1%")
    print(f"  - Throughput: >500 req/s")
    print(f"  - Cache hit rate: >80%")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print performance summary on test completion."""
    stats = environment.stats

    print("\n" + "="*60)
    print("LOAD TEST RESULTS")
    print("="*60)

    # Calculate metrics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    response_time_95 = stats.total.get_response_time_percentile(0.95)
    avg_response_time = stats.total.avg_response_time
    total_rps = stats.total.total_rps

    print(f"Total Requests: {total_requests:,}")
    print(f"Total Failures: {total_failures:,}")
    print(f"Error Rate: {error_rate:.2f}% {'✅ PASS' if error_rate < 1 else '❌ FAIL'} (Target: <1%)")
    print(f"\nResponse Times:")
    print(f"  Average: {avg_response_time:.2f}ms")
    print(f"  95th Percentile: {response_time_95:.2f}ms {'✅ PASS' if response_time_95 < 500 else '❌ FAIL'} (Target: <500ms)")
    print(f"\nThroughput:")
    print(f"  Requests/second: {total_rps:.2f} {'✅ PASS' if total_rps > 500 else '❌ FAIL'} (Target: >500 req/s)")

    print("\n" + "="*60)
    print("RECOMMENDATION:")
    if error_rate < 1 and response_time_95 < 500 and total_rps > 500:
        print("✅ System meets all performance targets")
        print("   Ready for production deployment")
    else:
        print("❌ System does not meet performance targets")
        print("   Review bottlenecks before production deployment")
    print("="*60 + "\n")
