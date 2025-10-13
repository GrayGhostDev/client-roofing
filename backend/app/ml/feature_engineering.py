"""
Feature Engineering Pipeline for NBA Model
Implements 2025 best practices with scikit-learn transformers
"""

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import pandas as pd
import numpy as np
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemporalFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract time-based features from lead data"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        Extract temporal features:
        - lead_age_days: Days since lead creation
        - days_since_last_contact: Days since last interaction
        - hour_of_first_contact: Hour of day when lead was created
        - is_weekend: Whether lead was created on weekend
        - day_of_week: Numeric day of week (0=Monday)
        """
        X = X.copy()

        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(X['created_at']):
            X['created_at'] = pd.to_datetime(X['created_at'])

        # Lead age
        X['lead_age_days'] = (pd.Timestamp.now() - X['created_at']).dt.days

        # Last contact recency
        if 'last_interaction_at' in X.columns:
            X['last_interaction_at'] = pd.to_datetime(X['last_interaction_at'], errors='coerce')
            X['days_since_last_contact'] = (
                pd.Timestamp.now() - X['last_interaction_at']
            ).dt.days
            X['days_since_last_contact'] = X['days_since_last_contact'].fillna(
                X['lead_age_days']  # If no interactions, use lead age
            )
        else:
            X['days_since_last_contact'] = X['lead_age_days']

        # Time of day features
        X['hour_of_first_contact'] = X['created_at'].dt.hour
        X['is_weekend'] = (X['created_at'].dt.dayofweek >= 5).astype(int)
        X['day_of_week'] = X['created_at'].dt.dayofweek

        logger.info("✅ Temporal features extracted")
        return X


class BehavioralFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract behavioral engagement features"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        Extract behavioral features:
        - interaction_count: Total number of interactions
        - email_open_rate: Proportion of emails opened
        - response_rate: Proportion of outbound contacts that got responses
        - appointment_show_rate: Proportion of appointments attended
        - avg_interaction_duration: Average interaction length in minutes
        """
        X = X.copy()

        # Interaction count
        X['interaction_count'] = X['interactions'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )

        # Email open rate
        X['email_open_rate'] = X.apply(self._calculate_email_open_rate, axis=1)

        # Response rate
        X['response_rate'] = X.apply(self._calculate_response_rate, axis=1)

        # Appointment show rate
        X['appointment_show_rate'] = X.apply(self._calculate_show_rate, axis=1)

        # Average interaction duration
        X['avg_interaction_duration'] = X.apply(self._calculate_avg_duration, axis=1)

        logger.info("✅ Behavioral features extracted")
        return X

    def _calculate_email_open_rate(self, row):
        """Calculate email open rate for a lead"""
        interactions = row.get('interactions', [])
        if not isinstance(interactions, list):
            return 0.0

        emails = [i for i in interactions if i.get('type') == 'email']
        if not emails:
            return 0.0

        opened = sum(1 for e in emails if e.get('opened', False))
        return opened / len(emails)

    def _calculate_response_rate(self, row):
        """Calculate response rate for outbound communications"""
        interactions = row.get('interactions', [])
        if not isinstance(interactions, list):
            return 0.0

        outbound = [i for i in interactions if i.get('direction') == 'outbound']
        if not outbound:
            return 0.0

        responses = sum(1 for i in outbound if i.get('response_received', False))
        return responses / len(outbound)

    def _calculate_show_rate(self, row):
        """Calculate appointment show rate"""
        appointments = row.get('appointments', [])
        if not isinstance(appointments, list) or not appointments:
            return 0.0

        showed = sum(1 for a in appointments if a.get('completed', False))
        return showed / len(appointments)

    def _calculate_avg_duration(self, row):
        """Calculate average interaction duration in minutes"""
        interactions = row.get('interactions', [])
        if not isinstance(interactions, list):
            return 0.0

        durations = [i.get('duration_minutes', 0) for i in interactions]
        return np.mean(durations) if durations else 0.0


class EngagementScoreCalculator(BaseEstimator, TransformerMixin):
    """Calculate composite engagement and urgency scores"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        Calculate derived scores:
        - engagement_score: Weighted composite score (0-100)
        - urgency_score: Time-decay based urgency (0-100)
        - response_velocity: Recent interaction frequency
        """
        X = X.copy()

        # Engagement score (weighted average of key metrics)
        X['engagement_score'] = (
            X['interaction_count'].clip(0, 20) * 0.25 +  # Max 5 points
            X['email_open_rate'] * 20 * 0.20 +  # Max 4 points
            X['response_rate'] * 30 * 0.30 +  # Max 9 points
            X['appointment_show_rate'] * 30 * 0.25  # Max 7.5 points
        ).clip(0, 100)

        # Urgency score (exponential decay based on recency)
        X['urgency_score'] = 100 * np.exp(-X['days_since_last_contact'] / 7.0)

        # Response velocity (interactions per day since creation)
        X['response_velocity'] = X['interaction_count'] / (X['lead_age_days'] + 1)

        logger.info("✅ Engagement scores calculated")
        return X


class PropertyFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract property-related features"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        Extract property features:
        - property_value_tier: Categorize property value
        - zip_code_prefix: First 3 digits of zip code (for geographic clustering)
        - has_property_value: Whether property value is available
        """
        X = X.copy()

        # Property value tier
        if 'estimated_value' in X.columns:
            X['property_value_tier'] = pd.cut(
                X['estimated_value'],
                bins=[0, 250000, 500000, 750000, 1000000, float('inf')],
                labels=['budget', 'mid', 'premium', 'luxury', 'ultra_luxury']
            ).astype(str)

            X['has_property_value'] = X['estimated_value'].notna().astype(int)
        else:
            X['property_value_tier'] = 'unknown'
            X['has_property_value'] = 0

        # Zip code prefix (geographic clustering)
        if 'property_zip' in X.columns:
            X['zip_code_prefix'] = X['property_zip'].astype(str).str[:3]
        else:
            X['zip_code_prefix'] = '000'

        logger.info("✅ Property features extracted")
        return X


class LeadSourceFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract and enhance lead source features"""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        Extract source-related features:
        - source_category: Grouped source categories
        - is_paid_channel: Whether source is paid marketing
        - is_referral: Whether source is referral-based
        """
        X = X.copy()

        # Categorize sources
        paid_sources = ['google_ads', 'facebook_ads', 'instagram_ads', 'paid_search']
        referral_sources = ['referral', 'partner', 'word_of_mouth']
        organic_sources = ['organic_search', 'website', 'seo']

        X['is_paid_channel'] = X['source'].str.lower().isin(paid_sources).astype(int)
        X['is_referral'] = X['source'].str.lower().isin(referral_sources).astype(int)
        X['is_organic'] = X['source'].str.lower().isin(organic_sources).astype(int)

        # Source category
        def categorize_source(source):
            source_lower = str(source).lower()
            if source_lower in paid_sources:
                return 'paid'
            elif source_lower in referral_sources:
                return 'referral'
            elif source_lower in organic_sources:
                return 'organic'
            else:
                return 'other'

        X['source_category'] = X['source'].apply(categorize_source)

        logger.info("✅ Lead source features extracted")
        return X


def build_feature_pipeline(
    categorical_features: List[str] = None,
    numerical_features: List[str] = None
) -> Pipeline:
    """
    Build complete feature engineering pipeline

    Args:
        categorical_features: List of categorical feature names (if None, uses defaults)
        numerical_features: List of numerical feature names (if None, uses defaults)

    Returns:
        Scikit-learn Pipeline for feature transformation
    """

    # Default feature lists
    if categorical_features is None:
        categorical_features = [
            'source',
            'source_category',
            'property_value_tier',
            'zip_code_prefix',
            'assigned_to'
        ]

    if numerical_features is None:
        numerical_features = [
            'lead_age_days',
            'days_since_last_contact',
            'hour_of_first_contact',
            'is_weekend',
            'day_of_week',
            'interaction_count',
            'email_open_rate',
            'response_rate',
            'appointment_show_rate',
            'avg_interaction_duration',
            'engagement_score',
            'urgency_score',
            'response_velocity',
            'is_paid_channel',
            'is_referral',
            'is_organic',
            'has_property_value',
            'lead_score'
        ]

    # Preprocessing for different feature types
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='drop'  # Drop features not specified
    )

    # Full pipeline
    pipeline = Pipeline([
        ('temporal', TemporalFeatureExtractor()),
        ('behavioral', BehavioralFeatureExtractor()),
        ('engagement', EngagementScoreCalculator()),
        ('property', PropertyFeatureExtractor()),
        ('source', LeadSourceFeatureExtractor()),
        ('preprocessor', preprocessor)
    ])

    logger.info(f"✅ Feature pipeline built with {len(numerical_features)} numerical and {len(categorical_features)} categorical features")

    return pipeline


def get_feature_names(pipeline: Pipeline) -> List[str]:
    """
    Extract feature names from fitted pipeline

    Args:
        pipeline: Fitted scikit-learn Pipeline

    Returns:
        List of feature names after transformation
    """
    if not hasattr(pipeline, 'named_steps'):
        raise ValueError("Pipeline must have named_steps")

    preprocessor = pipeline.named_steps['preprocessor']

    # Get numerical feature names
    num_features = preprocessor.transformers_[0][2]

    # Get categorical feature names (after one-hot encoding)
    cat_transformer = preprocessor.transformers_[1][1]
    cat_feature_names = cat_transformer.get_feature_names_out(
        preprocessor.transformers_[1][2]
    )

    # Combine
    all_features = list(num_features) + list(cat_feature_names)

    return all_features


if __name__ == "__main__":
    """Example usage"""
    import sys
    sys.path.append('..')

    # Create sample data
    sample_data = pd.DataFrame({
        'id': ['lead_1', 'lead_2', 'lead_3'],
        'source': ['google_ads', 'referral', 'organic_search'],
        'created_at': pd.date_range('2025-01-01', periods=3, freq='D'),
        'last_interaction_at': pd.date_range('2025-01-05', periods=3, freq='D'),
        'assigned_to': ['rep_1', 'rep_2', 'rep_1'],
        'estimated_value': [500000, 750000, 300000],
        'property_zip': ['48302', '48304', '48307'],
        'lead_score': [75, 85, 60],
        'interactions': [
            [{'type': 'email', 'opened': True, 'duration_minutes': 5}],
            [{'type': 'call', 'direction': 'outbound', 'response_received': True, 'duration_minutes': 10}],
            []
        ],
        'appointments': [
            [{'completed': True}],
            [],
            []
        ]
    })

    # Build and fit pipeline
    pipeline = build_feature_pipeline()
    X_transformed = pipeline.fit_transform(sample_data)

    print(f"Input shape: {sample_data.shape}")
    print(f"Output shape: {X_transformed.shape}")
    print(f"Features: {get_feature_names(pipeline)}")
    print("\n✅ Feature engineering pipeline test successful!")
