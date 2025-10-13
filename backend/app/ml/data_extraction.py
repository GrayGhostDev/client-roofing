"""
Data Extraction Module for ML Training
Extracts and cleans historical CRM data from Supabase
"""

from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExtractor:
    """Extract and preprocess CRM data for ML model training"""

    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

        self.supabase = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")

    def extract_leads_data(self, months_back: int = 12) -> pd.DataFrame:
        """
        Extract historical lead data for ML training

        Args:
            months_back: Number of months of historical data to extract

        Returns:
            DataFrame with lead data including interactions, appointments, projects
        """
        cutoff_date = (datetime.now() - timedelta(days=30 * months_back)).isoformat()
        logger.info(f"Extracting leads data from {cutoff_date}")

        try:
            # Extract leads with related data
            response = self.supabase.table("leads").select(
                """
                id,
                source,
                status,
                created_at,
                assigned_to,
                first_name,
                last_name,
                email,
                phone,
                property_address,
                property_zip,
                estimated_value,
                lead_score,
                interactions (
                    id,
                    type,
                    timestamp,
                    outcome,
                    notes,
                    duration_minutes
                ),
                appointments (
                    id,
                    scheduled_at,
                    completed,
                    result,
                    rescheduled_count
                ),
                projects (
                    id,
                    value,
                    status,
                    closed_at,
                    contract_signed_at
                )
                """
            ).gte("created_at", cutoff_date).execute()

            if not response.data:
                logger.warning("⚠️ No lead data found in specified time range")
                return pd.DataFrame()

            df = pd.DataFrame(response.data)
            logger.info(f"✅ Extracted {len(df)} lead records")

            return df

        except Exception as e:
            logger.error(f"❌ Failed to extract leads data: {e}")
            raise

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess extracted data

        Args:
            df: Raw DataFrame from Supabase

        Returns:
            Cleaned DataFrame ready for feature engineering
        """
        if df.empty:
            logger.warning("⚠️ Empty DataFrame provided for cleaning")
            return df

        logger.info(f"Cleaning data... Initial shape: {df.shape}")

        # Handle missing values
        df['source'] = df['source'].fillna('unknown')
        df['assigned_to'] = df['assigned_to'].fillna('unassigned')
        df['property_zip'] = df['property_zip'].fillna('00000')
        df['estimated_value'] = df['estimated_value'].fillna(df['estimated_value'].median())
        df['lead_score'] = df['lead_score'].fillna(50)  # Default to medium score

        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=['id'])
        if len(df) < initial_count:
            logger.info(f"Removed {initial_count - len(df)} duplicate records")

        # Handle outliers in estimated_value (IQR method)
        if 'estimated_value' in df.columns and df['estimated_value'].notna().any():
            q1 = df['estimated_value'].quantile(0.25)
            q3 = df['estimated_value'].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_count = len(df[
                (df['estimated_value'] < lower_bound) | (df['estimated_value'] > upper_bound)
            ])

            if outlier_count > 0:
                logger.info(f"Capping {outlier_count} outlier values in estimated_value")
                df['estimated_value'] = df['estimated_value'].clip(lower_bound, upper_bound)

        # Convert timestamps to datetime
        date_columns = ['created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

        # Data quality report
        logger.info(f"✅ Data cleaning complete. Final shape: {df.shape}")
        logger.info(f"Missing values:\n{df.isnull().sum()}")

        return df

    def create_train_test_split(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        val_size: float = 0.1,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Create stratified train/validation/test splits

        Args:
            df: Cleaned DataFrame
            test_size: Proportion for test set
            val_size: Proportion for validation set
            random_state: Random seed for reproducibility

        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        from sklearn.model_selection import train_test_split

        if df.empty:
            raise ValueError("Cannot split empty DataFrame")

        # Ensure we have a stratification column
        if 'status' not in df.columns:
            logger.warning("'status' column not found, splitting without stratification")
            stratify_col = None
        else:
            stratify_col = df['status']

        # First split: separate test set
        train_val, test = train_test_split(
            df,
            test_size=test_size,
            stratify=stratify_col if stratify_col is not None else None,
            random_state=random_state
        )

        # Second split: separate validation from training
        val_proportion = val_size / (1 - test_size)  # Adjust proportion

        if stratify_col is not None:
            stratify_train_val = train_val['status']
        else:
            stratify_train_val = None

        train, val = train_test_split(
            train_val,
            test_size=val_proportion,
            stratify=stratify_train_val,
            random_state=random_state
        )

        logger.info(f"✅ Data split complete:")
        logger.info(f"  Training:   {len(train)} samples ({len(train)/len(df)*100:.1f}%)")
        logger.info(f"  Validation: {len(val)} samples ({len(val)/len(df)*100:.1f}%)")
        logger.info(f"  Test:       {len(test)} samples ({len(test)/len(df)*100:.1f}%)")

        return train, val, test

    def calculate_next_best_action(self, row: pd.Series) -> str:
        """
        Calculate ground truth next best action based on historical data
        This creates the target variable for supervised learning

        Args:
            row: Single lead record

        Returns:
            Next best action label
        """
        # Priority logic based on lead state
        status = row.get('status', '').lower()
        interactions = row.get('interactions', [])
        appointments = row.get('appointments', [])
        projects = row.get('projects', [])

        interaction_count = len(interactions) if isinstance(interactions, list) else 0
        has_appointment = len(appointments) > 0 if isinstance(appointments, list) else False
        has_project = len(projects) > 0 if isinstance(projects, list) else False

        # Decision tree logic
        if status in ['new', 'uncontacted']:
            return 'call_immediate'

        elif status == 'contacted' and interaction_count < 3:
            return 'email_nurture'

        elif status == 'interested' and not has_appointment:
            return 'schedule_appointment'

        elif status == 'appointment_set' or has_appointment:
            return 'send_proposal'

        elif status in ['proposal_sent', 'negotiating']:
            return 'follow_up_call'

        elif status in ['won', 'closed']:
            return 'no_action'

        elif status in ['lost', 'disqualified']:
            return 'no_action'

        else:
            # Default for uncertain cases
            return 'email_nurture'

    def enrich_with_target_variable(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add 'next_best_action' target variable to DataFrame

        Args:
            df: DataFrame with lead data

        Returns:
            DataFrame with added 'next_best_action' column
        """
        logger.info("Calculating next_best_action target variable...")

        df['next_best_action'] = df.apply(self.calculate_next_best_action, axis=1)

        # Distribution report
        action_dist = df['next_best_action'].value_counts()
        logger.info(f"Target variable distribution:\n{action_dist}")

        return df


def main():
    """Example usage of DataExtractor"""
    import sys

    print("=== ML Data Extraction Pipeline ===\n")

    try:
        # Initialize extractor
        extractor = DataExtractor()

        # Extract data
        df = extractor.extract_leads_data(months_back=12)

        if df.empty:
            print("❌ No data extracted. Check Supabase connection and data availability.")
            sys.exit(1)

        # Clean data
        df = extractor.clean_data(df)

        # Add target variable
        df = extractor.enrich_with_target_variable(df)

        # Create splits
        train, val, test = extractor.create_train_test_split(df)

        # Save to disk for model training
        output_dir = "data/processed"
        os.makedirs(output_dir, exist_ok=True)

        train.to_parquet(f"{output_dir}/train.parquet", index=False)
        val.to_parquet(f"{output_dir}/val.parquet", index=False)
        test.to_parquet(f"{output_dir}/test.parquet", index=False)

        print(f"\n✅ Data extraction complete!")
        print(f"Saved datasets to {output_dir}/")
        print(f"  - train.parquet: {len(train)} samples")
        print(f"  - val.parquet: {len(val)} samples")
        print(f"  - test.parquet: {len(test)} samples")

    except Exception as e:
        print(f"\n❌ Error during data extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
