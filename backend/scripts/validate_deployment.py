#!/usr/bin/env python3
"""
Validate Railway deployment and run smoke tests.

This script performs comprehensive validation of the deployed ML API:
- Health checks
- Endpoint availability
- Model predictions
- Database connectivity
- Cache operations
- Performance benchmarks

Usage:
    python scripts/validate_deployment.py --url https://your-api.railway.app
    python scripts/validate_deployment.py --url https://your-api.railway.app --full
"""

import argparse
import sys
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
DEFAULT_TIMEOUT = 30
PERFORMANCE_THRESHOLDS = {
    'health_check': 1.0,  # seconds
    'metrics': 2.0,
    'prediction': 5.0,
    'batch_prediction': 10.0
}


class DeploymentValidator:
    """Validates Railway deployment through comprehensive tests."""

    def __init__(self, base_url: str, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[Dict] = []

    def run_test(self, name: str, func) -> Tuple[bool, str, float]:
        """Run a single test and track results."""
        logger.info(f"🧪 Testing: {name}...")
        start_time = time.time()

        try:
            result = func()
            elapsed = time.time() - start_time

            if result:
                logger.info(f"✅ {name} - PASSED ({elapsed:.2f}s)")
                self.results.append({
                    'name': name,
                    'status': 'PASSED',
                    'elapsed': elapsed
                })
                return True, "PASSED", elapsed
            else:
                logger.error(f"❌ {name} - FAILED ({elapsed:.2f}s)")
                self.results.append({
                    'name': name,
                    'status': 'FAILED',
                    'elapsed': elapsed
                })
                return False, "FAILED", elapsed

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ {name} - ERROR: {str(e)} ({elapsed:.2f}s)")
            self.results.append({
                'name': name,
                'status': 'ERROR',
                'elapsed': elapsed,
                'error': str(e)
            })
            return False, f"ERROR: {str(e)}", elapsed

    def test_health_check(self) -> bool:
        """Test basic health check endpoint."""
        response = requests.get(
            f"{self.base_url}/api/v1/ml/health",
            timeout=self.timeout
        )

        if response.status_code != 200:
            logger.error(f"Health check failed: {response.status_code}")
            return False

        data = response.json()
        if data.get('status') != 'healthy':
            logger.error(f"Unhealthy status: {data}")
            return False

        # Check critical components
        required_components = ['database', 'cache', 'ml_model']
        for component in required_components:
            if component not in data.get('components', {}):
                logger.error(f"Missing component: {component}")
                return False

            if data['components'][component] != 'healthy':
                logger.error(f"Unhealthy component: {component}")
                return False

        logger.info(f"Health check details: {data}")
        return True

    def test_metrics_endpoint(self) -> bool:
        """Test Prometheus metrics endpoint."""
        response = requests.get(
            f"{self.base_url}/api/v1/ml/metrics",
            timeout=self.timeout
        )

        if response.status_code != 200:
            logger.error(f"Metrics endpoint failed: {response.status_code}")
            return False

        metrics_text = response.text

        # Check for key metrics
        required_metrics = [
            'http_requests_total',
            'http_request_duration_seconds',
            'ml_predictions_total'
        ]

        for metric in required_metrics:
            if metric not in metrics_text:
                logger.error(f"Missing metric: {metric}")
                return False

        logger.info(f"Metrics endpoint OK ({len(metrics_text)} bytes)")
        return True

    def test_single_prediction(self) -> bool:
        """Test single lead prediction endpoint."""
        # Sample lead data
        test_lead = {
            "lead_source": "google_ads",
            "property_value": 450000,
            "roof_age": 18,
            "damage_severity": "moderate",
            "insurance_claim": True,
            "contact_quality": 8,
            "response_time_minutes": 5,
            "zip_code": "48304"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/ml/predict",
            json=test_lead,
            timeout=self.timeout
        )

        if response.status_code != 200:
            logger.error(f"Prediction failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

        prediction = response.json()

        # Validate prediction structure
        required_fields = ['lead_id', 'conversion_probability', 'predicted_revenue', 'confidence']
        for field in required_fields:
            if field not in prediction:
                logger.error(f"Missing field in prediction: {field}")
                return False

        # Validate probability range
        prob = prediction['conversion_probability']
        if not (0 <= prob <= 1):
            logger.error(f"Invalid probability: {prob}")
            return False

        logger.info(f"Prediction: {prediction}")
        return True

    def test_batch_prediction(self) -> bool:
        """Test batch prediction endpoint."""
        # Sample batch of leads
        test_leads = [
            {
                "lead_source": "facebook_ads",
                "property_value": 350000,
                "roof_age": 15,
                "damage_severity": "minor",
                "insurance_claim": False,
                "contact_quality": 6,
                "response_time_minutes": 120,
                "zip_code": "48302"
            },
            {
                "lead_source": "referral",
                "property_value": 600000,
                "roof_age": 22,
                "damage_severity": "severe",
                "insurance_claim": True,
                "contact_quality": 9,
                "response_time_minutes": 2,
                "zip_code": "48304"
            }
        ]

        response = requests.post(
            f"{self.base_url}/api/v1/ml/predict/batch",
            json={"leads": test_leads},
            timeout=self.timeout
        )

        if response.status_code != 200:
            logger.error(f"Batch prediction failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

        predictions = response.json()

        if len(predictions) != len(test_leads):
            logger.error(f"Expected {len(test_leads)} predictions, got {len(predictions)}")
            return False

        logger.info(f"Batch predictions: {len(predictions)} leads processed")
        return True

    def test_model_info(self) -> bool:
        """Test model information endpoint."""
        response = requests.get(
            f"{self.base_url}/api/v1/ml/model/info",
            timeout=self.timeout
        )

        if response.status_code != 200:
            logger.error(f"Model info failed: {response.status_code}")
            return False

        info = response.json()

        # Validate model info structure
        required_fields = ['model_version', 'model_type', 'features', 'accuracy']
        for field in required_fields:
            if field not in info:
                logger.error(f"Missing field in model info: {field}")
                return False

        logger.info(f"Model: {info['model_version']} (accuracy: {info['accuracy']})")
        return True

    def test_performance(self) -> bool:
        """Test performance benchmarks."""
        # Test multiple predictions to measure performance
        test_lead = {
            "lead_source": "google_ads",
            "property_value": 450000,
            "roof_age": 18,
            "damage_severity": "moderate",
            "insurance_claim": True,
            "contact_quality": 8,
            "response_time_minutes": 5,
            "zip_code": "48304"
        }

        num_requests = 10
        response_times = []

        for i in range(num_requests):
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/ml/predict",
                json=test_lead,
                timeout=self.timeout
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                response_times.append(elapsed)

        if not response_times:
            logger.error("All performance test requests failed")
            return False

        # Calculate statistics
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        logger.info(f"Performance stats ({num_requests} requests):")
        logger.info(f"  Average: {avg_time:.3f}s")
        logger.info(f"  Min: {min_time:.3f}s")
        logger.info(f"  Max: {max_time:.3f}s")

        # Check against threshold
        threshold = PERFORMANCE_THRESHOLDS['prediction']
        if avg_time > threshold:
            logger.warning(f"Average response time ({avg_time:.3f}s) exceeds threshold ({threshold}s)")
            return False

        return True

    def print_summary(self):
        """Print test summary."""
        logger.info("=" * 60)
        logger.info("DEPLOYMENT VALIDATION SUMMARY")
        logger.info("=" * 60)

        passed = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        total = len(self.results)

        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"⚠️  Errors: {errors}")
        logger.info(f"Success Rate: {(passed / total * 100):.1f}%")

        logger.info("\n📊 Test Details:")
        for result in self.results:
            status_icon = {
                'PASSED': '✅',
                'FAILED': '❌',
                'ERROR': '⚠️'
            }.get(result['status'], '❓')

            logger.info(f"  {status_icon} {result['name']}: {result['status']} ({result['elapsed']:.2f}s)")
            if 'error' in result:
                logger.info(f"     Error: {result['error']}")

        logger.info("=" * 60)

        # Overall result
        if failed == 0 and errors == 0:
            logger.info("🎉 DEPLOYMENT VALIDATION: SUCCESS")
            logger.info("   All tests passed! Deployment is ready for production.")
            return True
        else:
            logger.error("💥 DEPLOYMENT VALIDATION: FAILED")
            logger.error("   Some tests failed. Review errors above.")
            return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Validate Railway ML API deployment'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Base URL of deployed API (e.g., https://your-api.railway.app)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=DEFAULT_TIMEOUT,
        help='Request timeout in seconds'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full test suite including performance tests'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Railway ML API Deployment Validation")
    logger.info("=" * 60)
    logger.info(f"Target URL: {args.url}")
    logger.info(f"Timeout: {args.timeout}s")
    logger.info(f"Full suite: {args.full}")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Initialize validator
    validator = DeploymentValidator(args.url, args.timeout)

    # Run core tests
    core_tests = [
        ("Health Check", validator.test_health_check),
        ("Metrics Endpoint", validator.test_metrics_endpoint),
        ("Model Info", validator.test_model_info),
        ("Single Prediction", validator.test_single_prediction),
        ("Batch Prediction", validator.test_batch_prediction),
    ]

    for name, test_func in core_tests:
        validator.run_test(name, test_func)

    # Run performance tests if requested
    if args.full:
        validator.run_test("Performance Benchmark", validator.test_performance)

    # Print summary and exit
    success = validator.print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
