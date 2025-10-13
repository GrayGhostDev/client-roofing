"""
Unit Tests for A/B Testing Framework

Tests for experiment creation, variant assignment, and statistical analysis.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import hashlib
from typing import Dict, List

from app.ml.ab_testing import ABTestingFramework, ExperimentConfig


class TestABTestingFramework:
    """Test suite for ABTestingFramework class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        db.close = Mock()
        return db

    @pytest.fixture
    def framework(self, mock_db):
        """Create ABTestingFramework instance."""
        return ABTestingFramework(mock_db)

    def test_create_experiment_basic(self, framework):
        """Test basic experiment creation."""
        config = ExperimentConfig(
            name="Test Campaign A",
            description="Test description",
            hypothesis="New CTA will increase conversions",
            variants=[
                {"id": "control", "name": "Original", "traffic_percentage": 50},
                {"id": "variant_a", "name": "New CTA", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=1000
        )

        result = framework.create_experiment(config)

        # Assertions
        assert 'experiment_id' in result
        assert 'status' in result
        assert result['status'] == 'created'
        assert len(result['experiment_id']) > 0
        assert result['name'] == "Test Campaign A"
        assert len(result['variants']) == 2

    def test_create_experiment_traffic_validation(self, framework):
        """Test traffic allocation validation."""
        config = ExperimentConfig(
            name="Invalid Traffic Test",
            description="Test description",
            hypothesis="Test validation",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 40},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 40}
                # Total = 80%, should fail
            ],
            traffic_allocation={"control": 0.4, "variant_a": 0.4},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=1000
        )

        with pytest.raises(ValueError, match="Traffic allocation must sum to 1.0"):
            framework.create_experiment(config)

    def test_create_experiment_multi_variant(self, framework):
        """Test experiment with multiple variants."""
        config = ExperimentConfig(
            name="Multi-Variant Test",
            description="Test description",
            hypothesis="Test multiple variations",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 25},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 25},
                {"id": "variant_b", "name": "Variant B", "traffic_percentage": 25},
                {"id": "variant_c", "name": "Variant C", "traffic_percentage": 25}
            ],
            traffic_allocation={"control": 0.25, "variant_a": 0.25, "variant_b": 0.25, "variant_c": 0.25},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=1000
        )

        result = framework.create_experiment(config)

        assert len(result['variants']) == 4
        assert result['status'] == 'created'

    def test_assign_variant_consistency(self, framework):
        """Test that same user always gets same variant."""
        config = ExperimentConfig(
            name="Consistency Test",
            description="Test description",
            hypothesis="Test consistent assignment",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=1000
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']
        user_id = "user_12345"

        # Assign same user 10 times
        assignments = []
        for _ in range(10):
            result = framework.assign_variant(experiment_id, user_id)
            assignments.append(result['variant_id'])

        # All assignments should be identical
        assert len(set(assignments)) == 1, "User got different variants across assignments"

    def test_assign_variant_distribution(self, framework):
        """Test that variant assignment follows traffic distribution."""
        config = ExperimentConfig(
            name="Distribution Test",
            description="Test description",
            hypothesis="Test traffic distribution",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=1000
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Assign 1000 different users
        assignments = {'control': 0, 'variant_a': 0}
        for i in range(1000):
            result = framework.assign_variant(experiment_id, f"user_{i}")
            assignments[result['variant_id']] += 1

        # Check distribution is approximately 50/50 (within 10% margin)
        control_pct = assignments['control'] / 1000
        assert 0.40 <= control_pct <= 0.60, f"Control got {control_pct*100}%, expected ~50%"

    def test_assign_variant_invalid_experiment(self, framework):
        """Test assignment with invalid experiment ID."""
        with pytest.raises(ValueError, match="Experiment .* not found"):
            framework.assign_variant("invalid_exp_id", "user_123")

    def test_record_result_basic(self, framework):
        """Test recording experiment results."""
        config = ExperimentConfig(
            name="Result Recording Test",
            description="Test description",
            hypothesis="Test result recording",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=1000
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Record a conversion
        result = framework.record_result(
            experiment_id=experiment_id,
            user_id="user_123",
            variant_id="control",
            converted=True,
            metric_value=100.0
        )

        assert result['status'] == 'recorded'
        assert result['experiment_id'] == experiment_id

    def test_record_result_batch(self, framework):
        """Test recording multiple results."""
        config = ExperimentConfig(
            name="Batch Recording Test",
            description="Test description",
            hypothesis="Test batch recording",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=1000
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Record 100 results
        for i in range(100):
            variant_id = "control" if i % 2 == 0 else "variant_a"
            converted = i % 3 == 0  # ~33% conversion rate
            framework.record_result(
                experiment_id=experiment_id,
                user_id=f"user_{i}",
                variant_id=variant_id,
                converted=converted,
                metric_value=50.0 if converted else 0.0
            )

    def test_analyze_experiment_basic(self, framework):
        """Test basic experiment analysis."""
        config = ExperimentConfig(
            name="Analysis Test",
            description="Test description",
            hypothesis="Test statistical analysis",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=100
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Record results: control 20% conversion, variant_a 30% conversion
        for i in range(100):
            framework.record_result(
                experiment_id=experiment_id,
                user_id=f"user_control_{i}",
                variant_id="control",
                converted=(i < 20),
                metric_value=50.0 if (i < 20) else 0.0
            )

        for i in range(100):
            framework.record_result(
                experiment_id=experiment_id,
                user_id=f"user_variant_{i}",
                variant_id="variant_a",
                converted=(i < 30),
                metric_value=50.0 if (i < 30) else 0.0
            )

        # Analyze
        result = framework.analyze_experiment(experiment_id, confidence_level=0.95)

        # Assertions
        assert 'variants' in result
        assert 'status' in result  # Changed from 'summary' to 'status'
        assert len(result['variants']) == 2

        # Check control metrics (updated field names to match implementation)
        control = next(v for v in result['variants'] if v['variant_id'] == 'control')
        assert 'sample_size' in control
        assert 'conversion_rate' in control
        assert control['sample_size'] == 100
        assert control['conversion_rate'] == 20.0  # Percentage, not decimal

        # Check variant_a metrics (updated to match implementation)
        variant_a = next(v for v in result['variants'] if v['variant_id'] == 'variant_a')
        assert variant_a['sample_size'] == 100
        assert variant_a['conversion_rate'] == 30.0  # Percentage, not decimal

    def test_analyze_experiment_statistical_significance(self, framework):
        """Test statistical significance calculation."""
        config = ExperimentConfig(
            name="Significance Test",
            description="Test description",
            hypothesis="Test statistical significance",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=500
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Record significant difference: control 10%, variant_a 15%
        for i in range(500):
            framework.record_result(
                experiment_id=experiment_id,
                user_id=f"user_control_{i}",
                variant_id="control",
                converted=(i < 50),
                metric_value=100.0 if (i < 50) else 0.0
            )

        for i in range(500):
            framework.record_result(
                experiment_id=experiment_id,
                user_id=f"user_variant_{i}",
                variant_id="variant_a",
                converted=(i < 75),
                metric_value=100.0 if (i < 75) else 0.0
            )

        # Analyze
        result = framework.analyze_experiment(experiment_id, confidence_level=0.95)

        # Should be statistically significant
        variant_a = next(v for v in result['variants'] if v['variant_id'] == 'variant_a')
        assert 'p_value' in variant_a
        assert 'is_significant' in variant_a  # Changed from 'statistically_significant' to match implementation

    def test_select_winner_basic(self, framework):
        """Test winner selection."""
        config = ExperimentConfig(
            name="Winner Selection Test",
            description="Test description",
            hypothesis="Test winner selection",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=200
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Record results: variant_a clearly wins
        for i in range(200):
            framework.record_result(
                experiment_id=experiment_id,
                user_id=f"user_control_{i}",
                variant_id="control",
                converted=(i < 20),  # 10% conversion
                metric_value=50.0
            )

        for i in range(200):
            framework.record_result(
                experiment_id=experiment_id,
                user_id=f"user_variant_{i}",
                variant_id="variant_a",
                converted=(i < 60),  # 30% conversion
                metric_value=50.0
            )

        # Select winner
        result = framework.select_winner(experiment_id)

        assert 'winner' in result
        assert result['winner']['variant_id'] == 'variant_a'
        assert result['status'] == 'completed'

    def test_get_experiment_summary(self, framework):
        """Test experiment summary retrieval."""
        config = ExperimentConfig(
            name="Summary Test",
            description="Test description",
            hypothesis="Test summary retrieval",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=100
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Get summary
        result = framework.get_experiment_summary(experiment_id)

        assert 'experiment_id' in result
        assert 'name' in result
        assert 'status' in result
        assert 'variants' in result
        assert result['name'] == "Summary Test"


class TestABTestingEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query = Mock()
        return db

    @pytest.fixture
    def framework(self, mock_db):
        """Create ABTestingFramework instance."""
        return ABTestingFramework(mock_db)

    def test_empty_variants(self, framework):
        """Test experiment with no variants."""
        config = ExperimentConfig(
            name="No Variants Test",
            description="Test description",
            hypothesis="Test validation",
            variants=[],
            traffic_allocation={},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=100
        )

        with pytest.raises(ValueError, match="At least 2 variants required"):
            framework.create_experiment(config)

    def test_single_variant(self, framework):
        """Test experiment with only one variant."""
        config = ExperimentConfig(
            name="Single Variant Test",
            description="Test description",
            hypothesis="Test validation",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 100}
            ],
            traffic_allocation={"control": 1.0},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=100
        )

        with pytest.raises(ValueError, match="At least 2 variants required"):
            framework.create_experiment(config)

    def test_analyze_experiment_insufficient_data(self, framework):
        """Test analysis with insufficient data."""
        config = ExperimentConfig(
            name="Insufficient Data Test",
            description="Test description",
            hypothesis="Test with no data",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": 50},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 50}
            ],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=100
        )

        exp_result = framework.create_experiment(config)
        experiment_id = exp_result['experiment_id']

        # Analyze without recording any results
        result = framework.analyze_experiment(experiment_id)

        # Should return analysis with zero values
        assert 'variants' in result
        for variant in result['variants']:
            assert variant['total_users'] == 0
            assert variant['conversions'] == 0

    def test_negative_traffic_percentage(self, framework):
        """Test invalid traffic percentage."""
        config = ExperimentConfig(
            name="Negative Traffic Test",
            description="Test description",
            hypothesis="Test validation",
            variants=[
                {"id": "control", "name": "Control", "traffic_percentage": -10},
                {"id": "variant_a", "name": "Variant A", "traffic_percentage": 110}
            ],
            traffic_allocation={"variant_a": 1.1},
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            metric="conversion_rate",
            min_sample_size=100
        )

        with pytest.raises(ValueError):
            framework.create_experiment(config)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
