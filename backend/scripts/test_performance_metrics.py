"""
Performance Testing Script for Phase D
Measures page load times, API response times, and query performance
Version: 1.0.0
Date: 2025-10-10
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, List
import statistics

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from sqlalchemy import text


class PerformanceMetrics:
    """Measure and track performance metrics"""

    def __init__(self):
        self.results = []
        self.db = next(get_db())

    def measure_query(self, query: str, description: str, iterations: int = 10) -> Dict:
        """Measure query performance over multiple iterations"""
        times = []

        print(f"\n🔍 Testing: {description}")
        print(f"  Iterations: {iterations}")

        for i in range(iterations):
            start = time.time()
            result = self.db.execute(text(query))
            _ = result.fetchall()  # Force query execution
            elapsed = (time.time() - start) * 1000  # Convert to milliseconds
            times.append(elapsed)

        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)

        result = {
            'description': description,
            'query': query,
            'iterations': iterations,
            'avg_ms': avg_time,
            'min_ms': min_time,
            'max_ms': max_time,
            'median_ms': median_time,
            'passed': avg_time < 500  # Target: <500ms average
        }

        self.results.append(result)

        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {status} - Avg: {avg_time:.2f}ms | Min: {min_time:.2f}ms | Max: {max_time:.2f}ms | Median: {median_time:.2f}ms")

        return result

    def test_basic_queries(self):
        """Test basic query performance"""
        print("\n" + "="*80)
        print("PHASE D: BASIC QUERY PERFORMANCE TESTS")
        print("="*80)

        # Test 1: Simple count
        self.measure_query(
            "SELECT COUNT(*) FROM leads WHERE is_deleted = false",
            "Simple COUNT query (all leads)"
        )

        # Test 2: Select all leads
        self.measure_query(
            "SELECT * FROM leads WHERE is_deleted = false LIMIT 100",
            "SELECT first 100 leads"
        )

        # Test 3: Filter by temperature
        self.measure_query(
            "SELECT * FROM leads WHERE temperature = 'hot' AND is_deleted = false",
            "Filter leads by HOT temperature"
        )

        # Test 4: Filter by status
        self.measure_query(
            "SELECT * FROM leads WHERE status = 'qualified' AND is_deleted = false",
            "Filter leads by QUALIFIED status"
        )

        # Test 5: Sort by lead score
        self.measure_query(
            "SELECT * FROM leads WHERE is_deleted = false ORDER BY lead_score DESC LIMIT 50",
            "Sort leads by lead_score (DESC)"
        )

    def test_complex_queries(self):
        """Test complex query performance"""
        print("\n" + "="*80)
        print("PHASE D: COMPLEX QUERY PERFORMANCE TESTS")
        print("="*80)

        # Test 1: Multiple filters
        self.measure_query(
            """SELECT * FROM leads
               WHERE temperature = 'hot'
               AND status = 'qualified'
               AND lead_score >= 70
               AND is_deleted = false""",
            "Multiple filters (temperature + status + score)"
        )

        # Test 2: Aggregation
        self.measure_query(
            """SELECT temperature, COUNT(*) as count, AVG(lead_score) as avg_score
               FROM leads
               WHERE is_deleted = false
               GROUP BY temperature""",
            "Aggregation (GROUP BY temperature)"
        )

        # Test 3: Search-like query
        self.measure_query(
            """SELECT * FROM leads
               WHERE (first_name ILIKE '%john%' OR last_name ILIKE '%john%' OR email ILIKE '%john%')
               AND is_deleted = false""",
            "Search query (ILIKE name/email)"
        )

        # Test 4: City filter with sorting
        self.measure_query(
            """SELECT * FROM leads
               WHERE city IN ('Bloomfield Hills', 'Birmingham', 'Grosse Pointe')
               AND is_deleted = false
               ORDER BY property_value DESC
               LIMIT 25""",
            "Premium cities filter with sorting"
        )

    def test_pagination_queries(self):
        """Test pagination performance"""
        print("\n" + "="*80)
        print("PHASE D: PAGINATION PERFORMANCE TESTS")
        print("="*80)

        # Test 1: First page
        self.measure_query(
            "SELECT * FROM leads WHERE is_deleted = false ORDER BY created_at DESC LIMIT 25",
            "Pagination - Page 1 (LIMIT 25)"
        )

        # Test 2: Middle page
        self.measure_query(
            "SELECT * FROM leads WHERE is_deleted = false ORDER BY created_at DESC LIMIT 25 OFFSET 50",
            "Pagination - Page 3 (OFFSET 50, LIMIT 25)"
        )

        # Test 3: Last page
        self.measure_query(
            "SELECT * FROM leads WHERE is_deleted = false ORDER BY created_at DESC LIMIT 25 OFFSET 100",
            "Pagination - Last page (OFFSET 100, LIMIT 25)"
        )

    def test_dashboard_statistics(self):
        """Test dashboard statistics queries"""
        print("\n" + "="*80)
        print("PHASE D: DASHBOARD STATISTICS QUERIES")
        print("="*80)

        # Test 1: Temperature distribution
        self.measure_query(
            """SELECT temperature, COUNT(*) as count
               FROM leads
               WHERE is_deleted = false
               GROUP BY temperature""",
            "Temperature distribution (dashboard stats)"
        )

        # Test 2: Source distribution
        self.measure_query(
            """SELECT source, COUNT(*) as count
               FROM leads
               WHERE is_deleted = false
               GROUP BY source
               ORDER BY count DESC""",
            "Source distribution (dashboard stats)"
        )

        # Test 3: Monthly leads trend
        self.measure_query(
            """SELECT DATE_TRUNC('month', created_at) as month, COUNT(*) as count
               FROM leads
               WHERE is_deleted = false
               GROUP BY month
               ORDER BY month DESC
               LIMIT 6""",
            "Monthly leads trend (last 6 months)"
        )

        # Test 4: Average property value by city
        self.measure_query(
            """SELECT city, COUNT(*) as count, AVG(property_value) as avg_value
               FROM leads
               WHERE is_deleted = false
               GROUP BY city
               ORDER BY avg_value DESC
               LIMIT 10""",
            "Average property value by city (top 10)"
        )

    def generate_report(self):
        """Generate performance test report"""
        print("\n" + "="*80)
        print("PHASE D: PERFORMANCE TEST SUMMARY")
        print("="*80)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests

        print(f"\n📊 Overall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  ❌ Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

        # Performance thresholds
        all_avg_times = [r['avg_ms'] for r in self.results]
        overall_avg = statistics.mean(all_avg_times)
        overall_max = max(all_avg_times)
        overall_min = min(all_avg_times)

        print(f"\n⏱️  Performance Metrics:")
        print(f"  Average Response Time: {overall_avg:.2f}ms")
        print(f"  Fastest Query: {overall_min:.2f}ms")
        print(f"  Slowest Query: {overall_max:.2f}ms")
        print(f"  Target Threshold: <500ms")

        if overall_avg < 500:
            print(f"\n✅ PERFORMANCE TARGET MET: {overall_avg:.2f}ms < 500ms")
        else:
            print(f"\n❌ PERFORMANCE TARGET MISSED: {overall_avg:.2f}ms >= 500ms")

        # Slowest queries
        print(f"\n🐌 Slowest Queries:")
        slowest = sorted(self.results, key=lambda x: x['avg_ms'], reverse=True)[:5]
        for i, result in enumerate(slowest, 1):
            print(f"  {i}. {result['description']}: {result['avg_ms']:.2f}ms")

        # Failed queries
        if failed_tests > 0:
            print(f"\n❌ Failed Queries (exceeded 500ms threshold):")
            failed = [r for r in self.results if not r['passed']]
            for result in failed:
                print(f"  • {result['description']}: {result['avg_ms']:.2f}ms")

        # Database info
        print(f"\n📦 Database Information:")
        result = self.db.execute(text("SELECT COUNT(*) FROM leads WHERE is_deleted = false"))
        lead_count = result.scalar()
        print(f"  Total Leads: {lead_count}")

        result = self.db.execute(text("SELECT COUNT(DISTINCT city) FROM leads WHERE is_deleted = false"))
        city_count = result.scalar()
        print(f"  Unique Cities: {city_count}")

        result = self.db.execute(text("SELECT COUNT(DISTINCT source) FROM leads WHERE is_deleted = false"))
        source_count = result.scalar()
        print(f"  Unique Sources: {source_count}")

    def close(self):
        """Close database connection"""
        self.db.close()


if __name__ == "__main__":
    print("="*80)
    print("PHASE D: PERFORMANCE METRICS TESTING")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    metrics = PerformanceMetrics()

    try:
        # Run all performance tests
        metrics.test_basic_queries()
        metrics.test_complex_queries()
        metrics.test_pagination_queries()
        metrics.test_dashboard_statistics()

        # Generate summary report
        metrics.generate_report()

        print("\n" + "="*80)
        print("✅ PERFORMANCE TESTING COMPLETE")
        print("="*80)
        print()

    except Exception as e:
        print(f"\n❌ Performance testing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        metrics.close()
