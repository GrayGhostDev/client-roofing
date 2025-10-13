"""
Next Best Action (NBA) Prediction Model
Recommends optimal action for each lead using Gradient Boosting
"""

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import RandomizedSearchCV
import joblib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NextBestActionModel:
    """
    NBA Model predicts optimal next action for each lead

    Actions:
    - call_immediate: Urgent phone call required
    - email_nurture: Send personalized email
    - schedule_appointment: Book consultation
    - send_proposal: Send pricing proposal
    - follow_up_call: Follow-up on previous contact
    - no_action: Lead not ready or closed
    """

    ACTIONS = [
        'call_immediate',
        'email_nurture',
        'schedule_appointment',
        'send_proposal',
        'follow_up_call',
        'no_action'
    ]

    def __init__(self, model_path: str = "./models"):
        """
        Initialize NBA model

        Args:
            model_path: Directory to save/load model files
        """
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True, parents=True)
        self.model: Optional[GradientBoostingClassifier] = None
        self.feature_names: List[str] = []
        self.version: str = "1.0"
        self.trained_at: Optional[str] = None

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        hyperparameter_search: bool = True,
        n_iter: int = 20
    ) -> 'NextBestActionModel':
        """
        Train NBA model with optional hyperparameter optimization

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            hyperparameter_search: Whether to perform hyperparameter tuning
            n_iter: Number of iterations for random search

        Returns:
            Self for method chaining
        """
        logger.info("=" * 50)
        logger.info("Starting NBA Model Training")
        logger.info("=" * 50)

        # Validate input
        if X_train.shape[0] != y_train.shape[0]:
            raise ValueError(f"X_train ({X_train.shape[0]}) and y_train ({y_train.shape[0]}) must have same length")

        logger.info(f"Training samples: {X_train.shape[0]}")
        logger.info(f"Validation samples: {X_val.shape[0]}")
        logger.info(f"Features: {X_train.shape[1]}")
        logger.info(f"Classes: {np.unique(y_train)}")

        if hyperparameter_search:
            logger.info(f"\nPerforming hyperparameter optimization ({n_iter} iterations)...")
            self.model = self._hyperparameter_search(X_train, y_train, n_iter)
        else:
            logger.info("\nTraining with default hyperparameters...")
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=5,
                random_state=42,
                verbose=1
            )
            self.model.fit(X_train, y_train)

        # Validate
        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        logger.info(f"\n{'='*50}")
        logger.info(f"Training Accuracy:   {train_score:.4f}")
        logger.info(f"Validation Accuracy: {val_score:.4f}")
        logger.info(f"{'='*50}")

        # Check for overfitting
        if train_score - val_score > 0.10:
            logger.warning("⚠️  Potential overfitting detected (train-val gap > 10%)")

        self.trained_at = datetime.now().isoformat()

        return self

    def _hyperparameter_search(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        n_iter: int
    ) -> GradientBoostingClassifier:
        """
        Perform randomized hyperparameter search

        Args:
            X_train: Training features
            y_train: Training labels
            n_iter: Number of search iterations

        Returns:
            Best model from search
        """
        param_dist = {
            'n_estimators': [100, 200, 300, 400],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7, 9],
            'min_samples_split': [2, 5, 10, 20],
            'min_samples_leaf': [1, 2, 4, 8],
            'subsample': [0.8, 0.9, 1.0],
            'max_features': ['sqrt', 'log2', None]
        }

        base_model = GradientBoostingClassifier(random_state=42)

        search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            random_state=42,
            verbose=1
        )

        search.fit(X_train, y_train)

        logger.info(f"\nBest hyperparameters found:")
        for param, value in search.best_params_.items():
            logger.info(f"  {param}: {value}")

        logger.info(f"\nBest cross-validation F1 score: {search.best_score_:.4f}")

        return search.best_estimator_

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        detailed: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive model evaluation

        Args:
            X_test: Test features
            y_test: Test labels
            detailed: Whether to include detailed metrics

        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        logger.info("\n" + "=" * 50)
        logger.info("NBA Model Evaluation")
        logger.info("=" * 50)

        y_pred = self.model.predict(X_test)

        # Overall metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)

        # Per-class metrics
        class_report = classification_report(
            y_test, y_pred, output_dict=True, zero_division=0
        )

        # Feature importance
        feature_importance = self.model.feature_importances_

        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': cm.tolist(),
            'class_report': class_report,
            'feature_importance': feature_importance.tolist(),
            'n_test_samples': len(y_test)
        }

        # Log results
        logger.info(f"\nOverall Metrics:")
        logger.info(f"  Accuracy:  {accuracy:.4f}")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall:    {recall:.4f}")
        logger.info(f"  F1 Score:  {f1:.4f}")

        if detailed:
            logger.info(f"\nPer-Class Metrics:")
            for action in self.ACTIONS:
                if action in class_report:
                    logger.info(f"  {action}:")
                    logger.info(f"    Precision: {class_report[action]['precision']:.4f}")
                    logger.info(f"    Recall:    {class_report[action]['recall']:.4f}")
                    logger.info(f"    F1:        {class_report[action]['f1-score']:.4f}")
                    logger.info(f"    Support:   {int(class_report[action]['support'])}")

        logger.info("\n" + "=" * 50)

        return metrics

    def predict(
        self,
        X: np.ndarray,
        return_probabilities: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Predict next best action with confidence scores

        Args:
            X: Features for prediction
            return_probabilities: Whether to include probability distribution

        Returns:
            List of predictions with action and confidence
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() or load() first.")

        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)

        results = []
        for i, (pred, probs) in enumerate(zip(predictions, probabilities)):
            result = {
                'action': pred,
                'confidence': float(probs.max())
            }

            if return_probabilities:
                result['all_probabilities'] = {
                    action: float(prob)
                    for action, prob in zip(self.model.classes_, probs)
                }

            results.append(result)

        return results

    def predict_single(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Predict for a single sample (convenience method)

        Args:
            X: Single sample features

        Returns:
            Prediction dictionary
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        predictions = self.predict(X, return_probabilities=True)
        return predictions[0]

    def get_feature_importance(
        self,
        feature_names: Optional[List[str]] = None,
        top_n: int = 10
    ) -> pd.DataFrame:
        """
        Get feature importance rankings

        Args:
            feature_names: List of feature names
            top_n: Number of top features to return

        Returns:
            DataFrame with features and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained")

        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(self.model.feature_importances_))]

        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False).head(top_n)

        return importance_df

    def save(self, version: Optional[str] = None) -> Path:
        """
        Save model using joblib with protocol=5 (2025 best practice)

        Args:
            version: Model version string (defaults to self.version)

        Returns:
            Path to saved model file
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")

        if version is None:
            version = self.version

        # Save model with joblib (memory efficient protocol=5)
        model_file = self.model_path / f"nba_model_v{version}.joblib"
        joblib.dump(self.model, model_file, protocol=5)

        # Save metadata
        metadata = {
            'version': version,
            'classes': list(self.model.classes_),
            'n_features': int(self.model.n_features_in_),
            'n_estimators': int(self.model.n_estimators),
            'max_depth': int(self.model.max_depth),
            'learning_rate': float(self.model.learning_rate),
            'trained_at': self.trained_at,
            'feature_names': self.feature_names
        }

        metadata_file = self.model_path / f"nba_model_v{version}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Model saved:")
        logger.info(f"   Model: {model_file}")
        logger.info(f"   Metadata: {metadata_file}")

        return model_file

    def load(self, version: Optional[str] = None) -> 'NextBestActionModel':
        """
        Load model from disk

        Args:
            version: Model version to load (defaults to self.version)

        Returns:
            Self for method chaining
        """
        if version is None:
            version = self.version

        model_file = self.model_path / f"nba_model_v{version}.joblib"
        metadata_file = self.model_path / f"nba_model_v{version}_metadata.json"

        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        # Load model
        self.model = joblib.load(model_file)

        # Load metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                self.version = metadata.get('version', version)
                self.trained_at = metadata.get('trained_at')
                self.feature_names = metadata.get('feature_names', [])

        logger.info(f"✅ Model loaded from {model_file}")
        logger.info(f"   Version: {self.version}")
        logger.info(f"   Trained: {self.trained_at}")

        return self


# Placeholder classes for future weeks
class CLVPredictionModel:
    """Customer Lifetime Value prediction model (Week 9)"""
    def __init__(self):
        logger.info("CLVPredictionModel initialized (placeholder for Week 9)")


class ChurnPredictionModel:
    """Churn prediction model (Week 9)"""
    def __init__(self):
        logger.info("ChurnPredictionModel initialized (placeholder for Week 9)")


if __name__ == "__main__":
    """Example training workflow"""
    logger.info("NBA Model - Example Training Workflow")

    # Generate synthetic data for testing
    np.random.seed(42)
    n_samples = 1000
    n_features = 25

    X = np.random.randn(n_samples, n_features)
    y = np.random.choice(['call_immediate', 'email_nurture', 'schedule_appointment'], n_samples)

    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    # Train model
    nba_model = NextBestActionModel()
    nba_model.train(X_train, y_train, X_val, y_val, hyperparameter_search=False)

    # Evaluate
    metrics = nba_model.evaluate(X_test, y_test)

    # Predict
    sample_prediction = nba_model.predict_single(X_test[0])
    logger.info(f"\nSample Prediction: {sample_prediction}")

    # Feature importance
    importance = nba_model.get_feature_importance(top_n=5)
    logger.info(f"\nTop 5 Features:\n{importance}")

    # Save model
    nba_model.save(version="test")

    logger.info("\n✅ Example workflow complete!")
