"""
A/B Testing Framework for ML Models

Provides experiment management, traffic splitting, and statistical analysis
for testing different model versions, features, and configurations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import numpy as np
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel, Field

from app.database import get_db


class ExperimentStatus(str, Enum):
    """Experiment status enum."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    WINNER_SELECTED = "winner_selected"


class VariantType(str, Enum):
    """Variant type enum."""
    CONTROL = "control"
    TREATMENT = "treatment"


class ExperimentConfig(BaseModel):
    """Experiment configuration model."""
    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    hypothesis: str = Field(..., description="What you're testing")
    metric: str = Field(..., description="Primary success metric")
    variants: List[Dict[str, Any]] = Field(..., description="Experiment variants")
    traffic_allocation: Dict[str, float] = Field(..., description="Traffic % per variant")
    min_sample_size: int = Field(100, description="Minimum samples per variant")
    significance_level: float = Field(0.05, description="Statistical significance threshold")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExperimentResult(BaseModel):
    """Experiment result model."""
    variant_id: str
    variant_name: str
    sample_size: int
    conversion_rate: float
    avg_metric_value: float
    confidence_interval: tuple
    is_winner: bool = False


class ABTestingFramework:
    """A/B Testing framework for ML experiments."""

    def __init__(self, db: Session):
        self.db = db
        self.experiments: Dict[str, ExperimentConfig] = {}
        self.results: Dict[str, List[Dict]] = {}

    def create_experiment(
        self,
        config: ExperimentConfig
    ) -> Dict:
        """
        Create a new A/B test experiment.

        Args:
            config: Experiment configuration

        Returns:
            Dict with experiment details
        """
        # Validate minimum variants
        if len(config.variants) < 2:
            raise ValueError("At least 2 variants required")

        # Generate experiment ID
        experiment_id = self._generate_experiment_id(config.name)

        # Validate traffic allocation
        total_traffic = sum(config.traffic_allocation.values())
        if not (0.99 <= total_traffic <= 1.01):  # Allow small rounding errors
            raise ValueError(f"Traffic allocation must sum to 1.0, got {total_traffic}")

        # Validate variants match allocation
        variant_ids = {v['id'] for v in config.variants}
        allocation_ids = set(config.traffic_allocation.keys())
        if variant_ids != allocation_ids:
            raise ValueError("Variant IDs don't match traffic allocation keys")

        # Store experiment
        self.experiments[experiment_id] = config

        # Initialize results storage
        self.results[experiment_id] = []

        return {
            'experiment_id': experiment_id,
            'name': config.name,
            'status': 'created',  # Return string status for API consistency
            'variants': config.variants,  # Include variants in response
            'created_at': datetime.utcnow().isoformat(),
            'config': config.dict()
        }

    def assign_variant(
        self,
        experiment_id: str,
        user_id: str
    ) -> Dict:
        """
        Assign a user to a variant using consistent hashing.

        Args:
            experiment_id: Experiment identifier
            user_id: User/lead identifier

        Returns:
            Dict with assigned variant details
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        config = self.experiments[experiment_id]

        # Consistent hashing for stable assignment
        hash_input = f"{experiment_id}:{user_id}".encode('utf-8')
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        assignment_score = (hash_value % 10000) / 10000.0

        # Assign to variant based on traffic allocation
        cumulative = 0.0
        assigned_variant = None

        for variant_id, traffic in sorted(config.traffic_allocation.items()):
            cumulative += traffic
            if assignment_score <= cumulative:
                assigned_variant = next(
                    v for v in config.variants if v['id'] == variant_id
                )
                break

        if not assigned_variant:
            # Fallback to control
            assigned_variant = next(
                v for v in config.variants if v.get('type') == VariantType.CONTROL
            )

        return {
            'experiment_id': experiment_id,
            'user_id': user_id,
            'variant_id': assigned_variant['id'],
            'variant_name': assigned_variant['name'],
            'variant_config': assigned_variant.get('config', {}),
            'assigned_at': datetime.utcnow().isoformat()
        }

    def record_result(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
        metric_value: float,
        converted: bool = False,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record experiment result for a user.

        Args:
            experiment_id: Experiment identifier
            user_id: User identifier
            variant_id: Variant identifier
            metric_value: Metric value (e.g., revenue, conversion time)
            converted: Whether user converted
            metadata: Additional metadata

        Returns:
            Dict confirming result recording
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        result = {
            'experiment_id': experiment_id,
            'user_id': user_id,
            'variant_id': variant_id,
            'metric_value': metric_value,
            'converted': converted,
            'recorded_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        self.results[experiment_id].append(result)

        return {
            'status': 'recorded',
            'result_id': len(self.results[experiment_id]),
            'experiment_id': experiment_id
        }

    def analyze_experiment(
        self,
        experiment_id: str,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Analyze experiment results and determine statistical significance.

        Args:
            experiment_id: Experiment identifier
            confidence_level: Confidence level for significance testing

        Returns:
            Dict with analysis results
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        config = self.experiments[experiment_id]
        results = self.results.get(experiment_id, [])

        if not results:
            return {
                'experiment_id': experiment_id,
                'status': 'insufficient_data',
                'message': 'No results recorded yet',
                'variants': []  # Include empty variants list
            }

        # Group results by variant
        variant_data = {}
        for variant in config.variants:
            variant_id = variant['id']
            variant_results = [r for r in results if r['variant_id'] == variant_id]

            if not variant_results:
                variant_data[variant_id] = {
                    'sample_size': 0,
                    'conversions': 0,
                    'conversion_rate': 0,
                    'metric_values': [],
                    'avg_metric': 0
                }
                continue

            conversions = sum(1 for r in variant_results if r['converted'])
            metric_values = [r['metric_value'] for r in variant_results]

            variant_data[variant_id] = {
                'sample_size': len(variant_results),
                'conversions': conversions,
                'conversion_rate': conversions / len(variant_results) if variant_results else 0,
                'metric_values': metric_values,
                'avg_metric': np.mean(metric_values) if metric_values else 0,
                'std_metric': np.std(metric_values) if len(metric_values) > 1 else 0
            }

        # Find control variant
        control_id = next(
            (v['id'] for v in config.variants if v.get('type') == VariantType.CONTROL),
            config.variants[0]['id']  # Fallback to first variant
        )

        # Perform statistical tests
        analysis_results = []
        winner_id = None
        max_lift = 0

        for variant in config.variants:
            variant_id = variant['id']
            data = variant_data[variant_id]

            # Calculate confidence interval for conversion rate
            if data['sample_size'] > 0:
                ci = self._calculate_confidence_interval(
                    data['conversion_rate'],
                    data['sample_size'],
                    confidence_level
                )
            else:
                ci = (0, 0)

            # Compare to control (if not control)
            if variant_id != control_id:
                control_data = variant_data[control_id]

                # Chi-square test for conversion rate
                contingency_table = [
                    [data['conversions'], data['sample_size'] - data['conversions']],
                    [control_data['conversions'], control_data['sample_size'] - control_data['conversions']]
                ]

                if min(data['sample_size'], control_data['sample_size']) >= config.min_sample_size:
                    chi2, p_value = stats.chi2_contingency(contingency_table)[:2]
                    is_significant = p_value < config.significance_level

                    # Calculate lift
                    if control_data['conversion_rate'] > 0:
                        lift = ((data['conversion_rate'] - control_data['conversion_rate']) /
                               control_data['conversion_rate'] * 100)
                    else:
                        lift = 0

                    # Track best performer
                    if is_significant and lift > max_lift:
                        max_lift = lift
                        winner_id = variant_id
                else:
                    p_value = None
                    is_significant = False
                    lift = 0
            else:
                p_value = None
                is_significant = False
                lift = 0

            analysis_results.append({
                'variant_id': variant_id,
                'variant_name': variant['name'],
                'sample_size': data['sample_size'],
                'conversion_rate': round(data['conversion_rate'] * 100, 2),
                'avg_metric_value': round(data['avg_metric'], 2),
                'confidence_interval': (round(ci[0] * 100, 2), round(ci[1] * 100, 2)),
                'p_value': round(p_value, 4) if p_value is not None else None,
                'is_significant': is_significant,
                'lift_vs_control': round(lift, 2),
                'is_winner': variant_id == winner_id if winner_id else False
            })

        # Determine experiment status
        total_samples = sum(d['sample_size'] for d in variant_data.values())
        min_samples_met = all(
            d['sample_size'] >= config.min_sample_size
            for d in variant_data.values()
        )

        if winner_id and min_samples_met:
            status = 'winner_identified'
            recommendation = f"Variant '{next(r['variant_name'] for r in analysis_results if r['variant_id'] == winner_id)}' is statistically significant winner"
        elif min_samples_met:
            status = 'no_significant_difference'
            recommendation = "No statistically significant difference found. Consider running longer or testing different variants."
        else:
            status = 'collecting_data'
            samples_needed = max(
                config.min_sample_size - d['sample_size']
                for d in variant_data.values()
            )
            recommendation = f"Need {samples_needed} more samples to reach minimum sample size"

        return {
            'experiment_id': experiment_id,
            'experiment_name': config.name,
            'status': status,
            'total_samples': total_samples,
            'variants': analysis_results,
            'winner': next((r for r in analysis_results if r['is_winner']), None),
            'recommendation': recommendation,
            'confidence_level': confidence_level,
            'analyzed_at': datetime.utcnow().isoformat()
        }

    def select_winner(
        self,
        experiment_id: str,
        winner_variant_id: Optional[str] = None
    ) -> Dict:
        """
        Select a winner and complete the experiment.
        If winner_variant_id not provided, auto-detect based on analysis.

        Args:
            experiment_id: Experiment identifier
            winner_variant_id: Optional winning variant ID (auto-detect if None)

        Returns:
            Dict confirming winner selection
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        config = self.experiments[experiment_id]

        # Auto-detect winner if not provided
        if winner_variant_id is None:
            analysis = self.analyze_experiment(experiment_id)
            if analysis['status'] == 'winner_identified' and analysis['winner']:
                winner_variant_id = analysis['winner']['variant_id']
            else:
                raise ValueError("No clear winner identified. Provide winner_variant_id manually or run experiment longer.")

        # Validate winner exists
        winner = next(
            (v for v in config.variants if v['id'] == winner_variant_id),
            None
        )

        if not winner:
            raise ValueError(f"Variant {winner_variant_id} not found in experiment")

        return {
            'experiment_id': experiment_id,
            'winner': {
                'variant_id': winner_variant_id,
                'variant_name': winner['name']
            },
            'status': 'completed',  # Return string status for API consistency
            'completed_at': datetime.utcnow().isoformat()
        }

    def get_experiment_summary(
        self,
        experiment_id: str
    ) -> Dict:
        """
        Get experiment summary with current status.

        Args:
            experiment_id: Experiment identifier

        Returns:
            Dict with experiment summary
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        config = self.experiments[experiment_id]
        results = self.results.get(experiment_id, [])

        # Calculate basic stats
        total_samples = len(results)
        conversions = sum(1 for r in results if r['converted'])
        conversion_rate = (conversions / total_samples * 100) if total_samples > 0 else 0

        # Samples per variant
        variant_samples = {}
        for variant in config.variants:
            variant_id = variant['id']
            count = sum(1 for r in results if r['variant_id'] == variant_id)
            variant_samples[variant['name']] = count

        # Determine experiment status
        if total_samples == 0:
            status = 'draft'
        elif total_samples >= config.min_sample_size * len(config.variants):
            status = 'active'
        else:
            status = 'collecting_data'

        return {
            'experiment_id': experiment_id,
            'name': config.name,
            'description': config.description,
            'hypothesis': config.hypothesis,
            'metric': config.metric,
            'status': status,  # Add status field
            'variants': config.variants,  # Include variants list
            'total_samples': total_samples,
            'overall_conversion_rate': round(conversion_rate, 2),
            'samples_per_variant': variant_samples,
            'min_sample_size': config.min_sample_size,
            'min_samples_met': total_samples >= config.min_sample_size * len(config.variants),
            'start_date': config.start_date.isoformat() if config.start_date else None,
            'end_date': config.end_date.isoformat() if config.end_date else None
        }

    # Helper methods
    def _generate_experiment_id(self, name: str) -> str:
        """Generate unique experiment ID."""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"exp_{timestamp}_{name_hash}"

    def _calculate_confidence_interval(
        self,
        proportion: float,
        sample_size: int,
        confidence_level: float = 0.95
    ) -> tuple:
        """
        Calculate confidence interval for proportion.

        Args:
            proportion: Sample proportion
            sample_size: Sample size
            confidence_level: Confidence level

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if sample_size == 0:
            return (0, 0)

        # Z-score for confidence level
        z_score = stats.norm.ppf((1 + confidence_level) / 2)

        # Standard error
        se = np.sqrt((proportion * (1 - proportion)) / sample_size)

        # Confidence interval
        margin = z_score * se
        lower = max(0, proportion - margin)
        upper = min(1, proportion + margin)

        return (lower, upper)


# Global instance (in production, use proper dependency injection)
_ab_testing_framework: Optional[ABTestingFramework] = None


def get_ab_testing_framework(db: Session = None) -> ABTestingFramework:
    """Get or create AB testing framework instance."""
    global _ab_testing_framework
    if _ab_testing_framework is None:
        _ab_testing_framework = ABTestingFramework(db or next(get_db()))
    return _ab_testing_framework
