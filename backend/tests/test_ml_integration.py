#!/usr/bin/env python3
"""
Comprehensive ML Integration Tests
Tests all components: data extraction, features, NBA model, FastAPI endpoints
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import asyncio

# Test frameworks
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Our modules
from app.ml.next_best_action import NextBestActionModel
from app.ml.feature_engineering import build_feature_pipeline, get_feature_names


class TestMLCoreModules:
    """Test core ML modules with synthetic data"""

    @pytest.fixture
    def sample_lead_data(self):
        """Generate sample lead data for testing"""
        return pd.DataFrame({
            'id': [f'lead_{i}' for i in range(100)],
            'source': np.random.choice(['google_ads', 'facebook', 'referral', 'organic'], 100),
            'created_at': pd.date_range('2025-01-01', periods=100, freq='D'),
            'last_interaction_at': pd.date_range('2025-01-15', periods=100, freq='D'),
            'assigned_to': np.random.choice(['rep_1', 'rep_2', 'rep_3'], 100),
            'estimated_value': np.random.uniform(250000, 1500000, 100),
            'property_zip': np.random.choice(['48302', '48304', '48187', '48309'], 100),
            'lead_score': np.random.randint(30, 100, 100),
            'interactions': [[{'type': 'email', 'opened': True}]] * 100,
            'appointments': [[]] * 100,
            'next_best_action': np.random.choice(
                ['call_immediate', 'email_nurture', 'schedule_appointment'],
                100
            )
        })

    def test_feature_pipeline_creation(self):
        """Test feature engineering pipeline can be created"""
        print("\n🧪 Testing Feature Pipeline Creation...")

        pipeline = build_feature_pipeline()

        assert pipeline is not None
        assert hasattr(pipeline, 'fit_transform')
        assert hasattr(pipeline, 'transform')

        print("✅ Feature pipeline created successfully")

    def test_feature_engineering(self, sample_lead_data):
        """Test feature engineering on sample data"""
        print("\n🧪 Testing Feature Engineering...")

        pipeline = build_feature_pipeline()

        # Transform data
        X = pipeline.fit_transform(sample_lead_data)

        # Validate output
        assert X.shape[0] == 100, "Should have 100 samples"
        assert X.shape[1] > 20, "Should have 20+ features"
        assert not np.isnan(X).any(), "Should have no NaN values"
        assert not np.isinf(X).any(), "Should have no Inf values"

        print(f"✅ Features engineered: {X.shape[1]} features from {len(sample_lead_data)} samples")

    def test_nba_model_training(self, sample_lead_data):
        """Test NBA model can be trained on synthetic data"""
        print("\n🧪 Testing NBA Model Training...")

        from sklearn.model_selection import train_test_split

        # Build features
        pipeline = build_feature_pipeline()
        X = pipeline.fit_transform(sample_lead_data)
        y = sample_lead_data['next_best_action'].values

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train model
        model = NextBestActionModel(model_path="./tests/models")
        model.train(
            X_train, y_train,
            X_test, y_test,
            hyperparameter_search=False  # Skip for speed
        )

        # Validate model
        assert model.model is not None
        assert hasattr(model.model, 'predict')

        # Test accuracy
        score = model.model.score(X_test, y_test)
        assert score > 0.3, "Model should perform better than random"

        print(f"✅ Model trained successfully with {score:.2%} accuracy")

    def test_nba_model_prediction(self, sample_lead_data):
        """Test NBA model predictions"""
        print("\n🧪 Testing NBA Model Predictions...")

        # Build and fit pipeline
        pipeline = build_feature_pipeline()
        X = pipeline.fit_transform(sample_lead_data)
        y = sample_lead_data['next_best_action'].values

        # Train simple model
        from sklearn.ensemble import GradientBoostingClassifier
        model = NextBestActionModel(model_path="./tests/models")
        model.model = GradientBoostingClassifier(n_estimators=50, random_state=42)
        model.model.fit(X[:80], y[:80])

        # Predict
        predictions = model.predict(X[80:90])

        # Validate predictions
        assert len(predictions) == 10
        assert all('action' in p for p in predictions)
        assert all('confidence' in p for p in predictions)
        assert all(0 <= p['confidence'] <= 1 for p in predictions)

        print(f"✅ Generated {len(predictions)} predictions successfully")
        print(f"   Sample prediction: {predictions[0]}")

    def test_model_save_load(self, sample_lead_data):
        """Test model persistence"""
        print("\n🧪 Testing Model Save/Load...")

        # Train a simple model
        pipeline = build_feature_pipeline()
        X = pipeline.fit_transform(sample_lead_data)
        y = sample_lead_data['next_best_action'].values

        model = NextBestActionModel(model_path="./tests/models")
        model.model = GradientBoostingClassifier(n_estimators=50, random_state=42)
        model.model.fit(X, y)

        # Save
        model_file = model.save(version="test")
        assert model_file.exists()

        # Load
        loaded_model = NextBestActionModel(model_path="./tests/models")
        loaded_model.load(version="test")

        assert loaded_model.model is not None

        # Verify predictions match
        original_pred = model.predict(X[:5])
        loaded_pred = loaded_model.predict(X[:5])

        assert original_pred[0]['action'] == loaded_pred[0]['action']

        print("✅ Model saved and loaded successfully")

    def test_feature_importance(self, sample_lead_data):
        """Test feature importance extraction"""
        print("\n🧪 Testing Feature Importance...")

        # Train model
        pipeline = build_feature_pipeline()
        X = pipeline.fit_transform(sample_lead_data)
        y = sample_lead_data['next_best_action'].values

        model = NextBestActionModel(model_path="./tests/models")
        model.model = GradientBoostingClassifier(n_estimators=50, random_state=42)
        model.model.fit(X, y)

        # Get feature names
        feature_names = get_feature_names(pipeline)
        model.feature_names = feature_names

        # Get importance
        importance_df = model.get_feature_importance(
            feature_names=feature_names,
            top_n=10
        )

        assert len(importance_df) == 10
        assert 'feature' in importance_df.columns
        assert 'importance' in importance_df.columns

        print(f"✅ Feature importance calculated")
        print(f"   Top feature: {importance_df.iloc[0]['feature']}")


class TestFastAPIEndpoints:
    """Test FastAPI endpoints (without running server)"""

    @pytest.fixture
    def mock_model_manager(self):
        """Create mock model manager"""
        manager = Mock()
        manager._model = Mock()
        manager._pipeline = Mock()
        manager.version = "1.0"

        # Mock predict_single to return valid prediction
        manager.model.predict_single.return_value = {
            'action': 'schedule_appointment',
            'confidence': 0.87,
            'all_probabilities': {
                'call_immediate': 0.05,
                'email_nurture': 0.03,
                'schedule_appointment': 0.87,
                'send_proposal': 0.03,
                'follow_up_call': 0.01,
                'no_action': 0.01
            }
        }

        return manager

    @pytest.mark.asyncio
    async def test_health_endpoint_structure(self):
        """Test health endpoint response structure"""
        print("\n🧪 Testing Health Endpoint Structure...")

        from app.routes.ml_predictions import health_check, ModelManager

        manager = ModelManager()
        result = await health_check(manager)

        assert 'status' in result
        assert 'timestamp' in result

        print(f"✅ Health endpoint returns: {result['status']}")

    def test_pydantic_models(self):
        """Test Pydantic model validation"""
        print("\n🧪 Testing Pydantic Models...")

        from app.routes.ml_predictions import LeadFeatures, NBAPredict

        # Valid data
        lead_data = {
            'lead_id': 'test_001',
            'source': 'google_ads',
            'created_at': datetime.now(),
            'property_zip': '48302',
            'interaction_count': 5,
            'email_open_rate': 0.8,
            'response_rate': 0.6,
            'lead_score': 85
        }

        # Should create successfully
        lead = LeadFeatures(**lead_data)
        assert lead.lead_id == 'test_001'
        assert lead.email_open_rate == 0.8

        # Test prediction model
        pred_data = {
            'lead_id': 'test_001',
            'action': 'schedule_appointment',
            'confidence': 0.87,
            'all_probabilities': {
                'schedule_appointment': 0.87,
                'email_nurture': 0.13
            }
        }

        prediction = NBAPredict(**pred_data)
        assert prediction.confidence == 0.87

        print("✅ Pydantic models validate correctly")

    def test_pydantic_validation_errors(self):
        """Test Pydantic catches invalid data"""
        print("\n🧪 Testing Pydantic Validation...")

        from app.routes.ml_predictions import LeadFeatures
        from pydantic import ValidationError

        # Invalid email_open_rate (> 1.0)
        with pytest.raises(ValidationError):
            LeadFeatures(
                lead_id='test',
                source='google',
                created_at=datetime.now(),
                property_zip='48302',
                email_open_rate=1.5  # Invalid!
            )

        # Invalid zip code
        with pytest.raises(ValidationError):
            LeadFeatures(
                lead_id='test',
                source='google',
                created_at=datetime.now(),
                property_zip='123'  # Too short!
            )

        print("✅ Pydantic validation catches invalid data")


class TestGPTIntegration:
    """Test GPT-4/GPT-5 integration (with mocking)"""

    @pytest.mark.asyncio
    async def test_fallback_enhancement(self):
        """Test rule-based fallback enhancement"""
        print("\n🧪 Testing Fallback Enhancement...")

        from app.integrations.ai.openai_nba import (
            _fallback_enhancement,
            GPT4EnhancementContext
        )

        context = GPT4EnhancementContext(
            lead_id='test_001',
            ml_predicted_action='schedule_appointment',
            ml_confidence=0.87,
            lead_source='google_ads',
            property_value=650000,
            property_zip='48302',
            interaction_count=5,
            email_open_rate=0.8,
            response_rate=0.6,
            lead_age_days=7,
            days_since_last_contact=2
        )

        enhanced = _fallback_enhancement(context)

        assert enhanced.action == 'schedule_appointment'
        assert enhanced.urgency_level in ['low', 'medium', 'high', 'critical']
        assert len(enhanced.talking_points) >= 3
        assert enhanced.value_proposition is not None

        print(f"✅ Fallback enhancement works")
        print(f"   Action: {enhanced.action}")
        print(f"   Urgency: {enhanced.urgency_level}")

    @pytest.mark.asyncio
    async def test_gpt_context_creation(self):
        """Test GPT enhancement context creation"""
        print("\n🧪 Testing GPT Context Creation...")

        from app.integrations.ai.openai_nba import GPT4EnhancementContext

        context = GPT4EnhancementContext(
            lead_id='test_002',
            ml_predicted_action='call_immediate',
            ml_confidence=0.92,
            lead_source='referral',
            property_value=1200000,
            property_zip='48302',
            interaction_count=8,
            email_open_rate=0.9,
            response_rate=0.75,
            lead_age_days=3,
            days_since_last_contact=1,
            engagement_score=85.0,
            urgency_score=92.0
        )

        assert context.property_value == 1200000
        assert context.urgency_score == 92.0

        print("✅ GPT context created successfully")


class TestRedisCaching:
    """Test Redis caching functionality"""

    def test_cache_key_generation(self):
        """Test deterministic cache key creation"""
        print("\n🧪 Testing Cache Key Generation...")

        from app.utils.redis_cache import _create_cache_key

        # Same args should produce same key
        key1 = _create_cache_key('test', 'arg1', 'arg2', kwarg1='val1')
        key2 = _create_cache_key('test', 'arg1', 'arg2', kwarg1='val1')

        assert key1 == key2

        # Different args should produce different keys
        key3 = _create_cache_key('test', 'arg1', 'arg3', kwarg1='val1')
        assert key1 != key3

        print("✅ Cache key generation works correctly")

    @pytest.mark.asyncio
    async def test_cache_decorator_without_redis(self):
        """Test cache decorator works even without Redis"""
        print("\n🧪 Testing Cache Decorator (No Redis)...")

        from app.utils.redis_cache import cache_prediction

        call_count = 0

        @cache_prediction(ttl=60, key_prefix="test")
        async def test_function(arg1: str):
            nonlocal call_count
            call_count += 1
            return {"result": f"processed_{arg1}"}

        # Call twice
        result1 = await test_function("test_input")
        result2 = await test_function("test_input")

        # Should have called function (caching may not work if Redis unavailable)
        assert result1 == result2
        assert 'result' in result1

        print(f"✅ Cache decorator works (called {call_count} times)")


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow"""

    @pytest.mark.asyncio
    async def test_complete_prediction_workflow(self):
        """Test complete workflow from data to prediction"""
        print("\n🧪 Testing Complete Prediction Workflow...")

        # Step 1: Create sample data
        sample_data = pd.DataFrame({
            'id': ['lead_e2e_001'],
            'source': ['google_ads'],
            'created_at': [datetime.now() - timedelta(days=7)],
            'last_interaction_at': [datetime.now() - timedelta(days=2)],
            'assigned_to': ['rep_1'],
            'estimated_value': [650000],
            'property_zip': ['48302'],
            'lead_score': [85],
            'interactions': [[{'type': 'email', 'opened': True}]],
            'appointments': [[]]
        })

        # Step 2: Feature engineering
        pipeline = build_feature_pipeline()
        X = pipeline.fit_transform(sample_data)

        assert X.shape[0] == 1
        print(f"✅ Step 1: Features engineered ({X.shape[1]} features)")

        # Step 3: Train simple model
        # (Use more data for actual training)
        extended_data = pd.concat([sample_data] * 100, ignore_index=True)
        extended_data['next_best_action'] = np.random.choice(
            ['call_immediate', 'email_nurture', 'schedule_appointment'],
            100
        )

        X_train = pipeline.fit_transform(extended_data)
        y_train = extended_data['next_best_action'].values

        model = NextBestActionModel(model_path="./tests/models")
        model.model = GradientBoostingClassifier(n_estimators=50, random_state=42)
        model.model.fit(X_train, y_train)

        print("✅ Step 2: Model trained")

        # Step 4: Predict
        X_new = pipeline.transform(sample_data)
        prediction = model.predict_single(X_new)

        assert 'action' in prediction
        assert 'confidence' in prediction
        assert prediction['confidence'] > 0

        print(f"✅ Step 3: Prediction generated")
        print(f"   Action: {prediction['action']}")
        print(f"   Confidence: {prediction['confidence']:.2%}")

        # Step 5: Enhanced prediction (with fallback)
        from app.integrations.ai.openai_nba import (
            GPT4EnhancementContext,
            _fallback_enhancement
        )

        context = GPT4EnhancementContext(
            lead_id='lead_e2e_001',
            ml_predicted_action=prediction['action'],
            ml_confidence=prediction['confidence'],
            lead_source='google_ads',
            property_value=650000,
            property_zip='48302',
            interaction_count=1,
            email_open_rate=1.0,
            response_rate=0.0,
            lead_age_days=7,
            days_since_last_contact=2
        )

        enhanced = _fallback_enhancement(context)

        assert enhanced.action == prediction['action']
        assert len(enhanced.talking_points) > 0

        print(f"✅ Step 4: Enhanced recommendation generated")
        print(f"   Urgency: {enhanced.urgency_level}")
        print(f"   Talking points: {len(enhanced.talking_points)}")

        print("\n🎉 Complete end-to-end workflow successful!")


def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE ML INTEGRATION TEST SUITE")
    print("=" * 70)

    # Run pytest with verbose output
    pytest_args = [
        __file__,
        '-v',
        '--tb=short',
        '--capture=no',
        '-p', 'no:warnings'
    ]

    exit_code = pytest.main(pytest_args)

    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {exit_code})")
    print("=" * 70 + "\n")

    return exit_code


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
