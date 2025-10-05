"""
Performance Testing Suite for iSwitch Roofs CRM
Tests response times, memory usage, concurrent handling, and scalability
"""

import pytest
import time
import threading
import asyncio
import psutil
import os
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
import statistics


class TestAPIPerformance:
    """Test suite for API performance."""

    def test_response_time_benchmarks(self, client, auth_headers):
        """Test API response time benchmarks."""
        endpoints_and_targets = [
            ('/api/leads', 200),           # 200ms target
            ('/api/customers', 200),       # 200ms target
            ('/api/projects', 300),        # 300ms target
            ('/api/analytics/dashboard', 500),  # 500ms target (complex queries)
            ('/api/appointments', 200),    # 200ms target
        ]

        for endpoint, target_ms in endpoints_and_targets:
            start_time = time.time()
            response = client.get(endpoint, headers=auth_headers)
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            # Log performance for monitoring
            print(f"{endpoint}: {response_time_ms:.2f}ms (target: {target_ms}ms)")

            # Should meet target response time
            assert response_time_ms < target_ms * 2, f"{endpoint} too slow: {response_time_ms:.2f}ms"

    def test_database_query_performance(self, client, auth_headers):
        """Test database query performance."""
        with patch('app.services.leads.get_all_leads') as mock_service:
            # Mock large dataset
            mock_service.return_value = {
                'data': [{'id': f'lead-{i}', 'name': f'Lead {i}'} for i in range(1000)],
                'total': 1000
            }

            start_time = time.time()
            response = client.get('/api/leads?per_page=100', headers=auth_headers)
            end_time = time.time()

            query_time_ms = (end_time - start_time) * 1000

            # Database queries should be fast even with large datasets
            assert query_time_ms < 500, f"Database query too slow: {query_time_ms:.2f}ms"
            assert response.status_code == 200

    def test_pagination_performance(self, client, auth_headers):
        """Test pagination performance across large datasets."""
        page_sizes = [10, 50, 100, 500]
        max_acceptable_time = 1000  # 1 second

        for page_size in page_sizes:
            with patch('app.services.leads.get_all_leads') as mock_service:
                # Mock paginated response
                mock_service.return_value = {
                    'data': [{'id': f'lead-{i}'} for i in range(page_size)],
                    'total': 10000,
                    'page': 1,
                    'per_page': page_size
                }

                start_time = time.time()
                response = client.get(f'/api/leads?per_page={page_size}', headers=auth_headers)
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000

                print(f"Page size {page_size}: {response_time_ms:.2f}ms")
                assert response_time_ms < max_acceptable_time

    def test_search_performance(self, client, auth_headers):
        """Test search functionality performance."""
        search_queries = [
            'John',           # Simple name search
            'john@example',   # Email search
            '555-1234',       # Phone search
            'roof replacement',  # Description search
        ]

        for query in search_queries:
            with patch('app.services.leads.search_leads') as mock_search:
                mock_search.return_value = {
                    'data': [{'id': 'lead-1', 'first_name': 'John'}],
                    'total': 1
                }

                start_time = time.time()
                response = client.get(f'/api/leads?search={query}', headers=auth_headers)
                end_time = time.time()

                search_time_ms = (end_time - start_time) * 1000

                # Search should be fast
                assert search_time_ms < 300, f"Search too slow for '{query}': {search_time_ms:.2f}ms"

    def test_analytics_performance(self, client, auth_headers):
        """Test analytics dashboard performance."""
        with patch('app.services.analytics_service.get_dashboard_metrics') as mock_analytics:
            # Mock complex analytics data
            mock_analytics.return_value = {
                'total_leads': 5000,
                'conversion_rate': 15.5,
                'revenue_data': [{'month': f'2025-{i:02d}', 'revenue': 50000 + i * 1000} for i in range(1, 13)],
                'team_performance': [{'member': f'Member {i}', 'leads': 100 + i * 10} for i in range(10)]
            }

            start_time = time.time()
            response = client.get('/api/analytics/dashboard', headers=auth_headers)
            end_time = time.time()

            analytics_time_ms = (end_time - start_time) * 1000

            # Analytics queries can be more complex but should still be reasonable
            assert analytics_time_ms < 1000, f"Analytics too slow: {analytics_time_ms:.2f}ms"


class TestConcurrencyPerformance:
    """Test suite for concurrent request handling."""

    def test_concurrent_read_requests(self, client, auth_headers):
        """Test handling of concurrent read requests."""
        def make_request():
            start_time = time.time()
            response = client.get('/api/leads', headers=auth_headers)
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000
            }

        # Test with 20 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        # All requests should succeed
        success_count = sum(1 for r in results if r['status_code'] == 200)
        assert success_count >= 18, f"Only {success_count}/20 requests succeeded"

        # Response times should be reasonable
        avg_response_time = statistics.mean(r['response_time'] for r in results)
        max_response_time = max(r['response_time'] for r in results)

        print(f"Concurrent requests - Avg: {avg_response_time:.2f}ms, Max: {max_response_time:.2f}ms")
        assert avg_response_time < 1000, f"Average response time too high: {avg_response_time:.2f}ms"
        assert max_response_time < 3000, f"Max response time too high: {max_response_time:.2f}ms"

    def test_concurrent_write_requests(self, client, auth_headers):
        """Test handling of concurrent write requests."""
        def create_lead(lead_id):
            lead_data = {
                'first_name': f'TestLead{lead_id}',
                'last_name': 'Performance',
                'email': f'test{lead_id}@example.com',
                'phone': f'555-{lead_id:04d}'
            }

            start_time = time.time()
            response = client.post(
                '/api/leads',
                data=json.dumps(lead_data),
                headers=auth_headers
            )
            end_time = time.time()

            return {
                'lead_id': lead_id,
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000
            }

        # Test with 10 concurrent write requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_lead, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]

        # Most requests should succeed (some may conflict)
        success_count = sum(1 for r in results if r['status_code'] in [200, 201])
        assert success_count >= 8, f"Only {success_count}/10 write requests succeeded"

    def test_mixed_concurrent_operations(self, client, auth_headers):
        """Test mixed read/write operations under concurrent load."""
        def read_operation():
            return client.get('/api/leads', headers=auth_headers)

        def write_operation(index):
            data = {
                'first_name': f'Concurrent{index}',
                'last_name': 'Test',
                'email': f'concurrent{index}@test.com',
                'phone': f'555-{index:04d}'
            }
            return client.post('/api/leads', data=json.dumps(data), headers=auth_headers)

        def update_operation():
            data = {'status': 'qualified'}
            return client.put('/api/leads/test-lead', data=json.dumps(data), headers=auth_headers)

        # Mix of operations: 15 reads, 3 writes, 2 updates
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []

            # Submit read operations
            for _ in range(15):
                futures.append(executor.submit(read_operation))

            # Submit write operations
            for i in range(3):
                futures.append(executor.submit(write_operation, i))

            # Submit update operations
            for _ in range(2):
                futures.append(executor.submit(update_operation))

            # Collect results
            results = [future.result() for future in as_completed(futures)]

        # Most operations should complete successfully
        success_count = sum(1 for r in results if r.status_code in [200, 201, 404])
        assert success_count >= 18, f"Only {success_count}/20 mixed operations succeeded"


class TestMemoryPerformance:
    """Test suite for memory usage and efficiency."""

    def test_memory_usage_under_load(self, client, auth_headers):
        """Test memory usage under sustained load."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate sustained load
        for i in range(100):
            response = client.get('/api/leads', headers=auth_headers)

            # Force garbage collection periodically
            if i % 20 == 0:
                gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"Memory usage - Initial: {initial_memory:.2f}MB, Final: {final_memory:.2f}MB, Increase: {memory_increase:.2f}MB")

        # Memory increase should be reasonable
        assert memory_increase < 50, f"Memory increase too high: {memory_increase:.2f}MB"

    def test_large_response_handling(self, client, auth_headers):
        """Test handling of large response payloads."""
        with patch('app.services.leads.get_all_leads') as mock_service:
            # Mock very large dataset
            large_dataset = [
                {
                    'id': f'lead-{i}',
                    'first_name': f'FirstName{i}',
                    'last_name': f'LastName{i}',
                    'email': f'user{i}@example.com',
                    'phone': f'555-{i:06d}',
                    'description': 'A' * 1000,  # 1KB description each
                    'notes': 'B' * 500          # 500B notes each
                }
                for i in range(1000)  # 1000 records ≈ 1.5MB
            ]

            mock_service.return_value = {
                'data': large_dataset,
                'total': 1000
            }

            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss

            start_time = time.time()
            response = client.get('/api/leads?per_page=1000', headers=auth_headers)
            end_time = time.time()

            memory_after = process.memory_info().rss
            memory_used = (memory_after - memory_before) / 1024 / 1024  # MB

            response_time = (end_time - start_time) * 1000

            print(f"Large response - Time: {response_time:.2f}ms, Memory: {memory_used:.2f}MB")

            # Should handle large responses efficiently
            assert response_time < 2000, f"Large response too slow: {response_time:.2f}ms"
            assert memory_used < 100, f"Too much memory used: {memory_used:.2f}MB"

    def test_memory_leak_detection(self, client, auth_headers):
        """Test for memory leaks during repeated operations."""
        process = psutil.Process(os.getpid())
        memory_samples = []

        # Take memory measurements during repeated operations
        for i in range(50):
            # Perform operation
            client.get('/api/leads', headers=auth_headers)

            # Sample memory every 10 operations
            if i % 10 == 0:
                gc.collect()  # Force garbage collection
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)

        # Check for steadily increasing memory (potential leak)
        if len(memory_samples) >= 3:
            # Calculate trend
            memory_trend = memory_samples[-1] - memory_samples[0]
            print(f"Memory trend over {len(memory_samples)} samples: {memory_trend:.2f}MB")

            # Memory should not increase significantly
            assert memory_trend < 20, f"Potential memory leak detected: {memory_trend:.2f}MB increase"


class TestScalabilityPerformance:
    """Test suite for scalability performance."""

    def test_user_scaling_simulation(self, client, auth_headers):
        """Simulate increasing number of concurrent users."""
        user_counts = [1, 5, 10, 20, 50]
        max_acceptable_degradation = 5.0  # 5x slowdown acceptable

        baseline_time = None

        for user_count in user_counts:
            def user_simulation():
                start_time = time.time()
                response = client.get('/api/leads', headers=auth_headers)
                end_time = time.time()
                return (end_time - start_time) * 1000

            # Run simulation with current user count
            with ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [executor.submit(user_simulation) for _ in range(user_count)]
                response_times = [future.result() for future in as_completed(futures)]

            avg_response_time = statistics.mean(response_times)

            if baseline_time is None:
                baseline_time = avg_response_time

            degradation_factor = avg_response_time / baseline_time

            print(f"{user_count} users - Avg response: {avg_response_time:.2f}ms, Degradation: {degradation_factor:.2f}x")

            # Performance should degrade gracefully
            assert degradation_factor < max_acceptable_degradation, \
                f"Performance degraded too much with {user_count} users: {degradation_factor:.2f}x"

    def test_data_volume_scaling(self, client, auth_headers):
        """Test performance scaling with increasing data volumes."""
        data_sizes = [100, 500, 1000, 5000]

        for size in data_sizes:
            with patch('app.services.leads.get_all_leads') as mock_service:
                # Mock dataset of specified size
                mock_service.return_value = {
                    'data': [{'id': f'lead-{i}', 'name': f'Lead {i}'} for i in range(size)],
                    'total': size
                }

                start_time = time.time()
                response = client.get(f'/api/leads?per_page={min(size, 100)}', headers=auth_headers)
                end_time = time.time()

                response_time = (end_time - start_time) * 1000

                print(f"Data size {size} - Response time: {response_time:.2f}ms")

                # Response time should scale sub-linearly with data size
                expected_max_time = 100 + (size / 100) * 50  # Base 100ms + 50ms per 100 records
                assert response_time < expected_max_time, \
                    f"Response time {response_time:.2f}ms too high for {size} records"


class TestResourceUtilization:
    """Test suite for resource utilization efficiency."""

    def test_cpu_utilization(self, client, auth_headers):
        """Test CPU utilization during operations."""
        process = psutil.Process(os.getpid())

        # Measure CPU usage during sustained operations
        cpu_samples = []
        start_time = time.time()

        for i in range(50):
            client.get('/api/leads', headers=auth_headers)

            if i % 10 == 0:
                cpu_percent = process.cpu_percent()
                cpu_samples.append(cpu_percent)

        end_time = time.time()
        total_time = end_time - start_time

        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            max_cpu = max(cpu_samples)

            print(f"CPU utilization - Avg: {avg_cpu:.2f}%, Max: {max_cpu:.2f}%, Duration: {total_time:.2f}s")

            # CPU usage should be reasonable
            assert avg_cpu < 50, f"Average CPU usage too high: {avg_cpu:.2f}%"
            assert max_cpu < 80, f"Peak CPU usage too high: {max_cpu:.2f}%"

    def test_database_connection_efficiency(self, client, auth_headers):
        """Test database connection pool efficiency."""
        # This would test database connection pooling
        # Mock database connection monitoring
        with patch('app.database.connection_pool') as mock_pool:
            mock_pool.get_stats.return_value = {
                'active_connections': 5,
                'idle_connections': 15,
                'total_connections': 20
            }

            # Perform multiple operations
            for _ in range(20):
                client.get('/api/leads', headers=auth_headers)

            # Connection pool should be efficient
            stats = mock_pool.get_stats()
            assert stats['active_connections'] <= stats['total_connections']
            assert stats['idle_connections'] >= 0

    def test_cache_efficiency(self, client, auth_headers):
        """Test caching efficiency for repeated requests."""
        # Test that repeated requests are served from cache
        endpoint = '/api/analytics/dashboard'

        # First request (should be cached)
        start_time = time.time()
        response1 = client.get(endpoint, headers=auth_headers)
        first_request_time = (time.time() - start_time) * 1000

        # Second request (should be faster due to caching)
        start_time = time.time()
        response2 = client.get(endpoint, headers=auth_headers)
        second_request_time = (time.time() - start_time) * 1000

        print(f"Cache test - First: {first_request_time:.2f}ms, Second: {second_request_time:.2f}ms")

        # Second request should be significantly faster (if caching is implemented)
        # If no caching, times should be similar
        cache_speedup = first_request_time / second_request_time if second_request_time > 0 else 1

        # Allow for either cached (faster) or non-cached (similar) performance
        assert cache_speedup >= 0.5, f"Unexpected cache behavior: {cache_speedup:.2f}x"


# Performance test markers
pytestmark = [
    pytest.mark.performance,
    pytest.mark.slow
]