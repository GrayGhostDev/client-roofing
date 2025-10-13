#!/usr/bin/env python3
"""
NBA Model Training Script
Complete end-to-end pipeline for training the Next Best Action model
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.ml.data_extraction import DataExtractor
from app.ml.feature_engineering import build_feature_pipeline, get_feature_names
from app.ml.next_best_action import NextBestActionModel
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main training pipeline"""
    print("\n" + "=" * 70)
    print("NBA MODEL TRAINING PIPELINE")
    print("=" * 70 + "\n")

    try:
        # Step 1: Extract and clean data
        print("📊 Step 1: Data Extraction")
        print("-" * 70)

        extractor = DataExtractor()
        df = extractor.extract_leads_data(months_back=12)

        if df.empty:
            logger.error("❌ No data extracted. Check Supabase connection.")
            return 1

        logger.info(f"✅ Extracted {len(df)} lead records")

        # Clean data
        df = extractor.clean_data(df)

        # Add target variable
        df = extractor.enrich_with_target_variable(df)

        # Create splits
        train_df, val_df, test_df = extractor.create_train_test_split(df)

        # Step 2: Feature Engineering
        print("\n🔧 Step 2: Feature Engineering")
        print("-" * 70)

        pipeline = build_feature_pipeline()

        logger.info("Transforming training data...")
        X_train = pipeline.fit_transform(train_df)
        y_train = train_df['next_best_action'].values

        logger.info("Transforming validation data...")
        X_val = pipeline.transform(val_df)
        y_val = val_df['next_best_action'].values

        logger.info("Transforming test data...")
        X_test = pipeline.transform(test_df)
        y_test = test_df['next_best_action'].values

        logger.info(f"✅ Feature engineering complete")
        logger.info(f"   Training set: {X_train.shape}")
        logger.info(f"   Validation set: {X_val.shape}")
        logger.info(f"   Test set: {X_test.shape}")

        # Get feature names for later analysis
        feature_names = get_feature_names(pipeline)
        logger.info(f"   Total features: {len(feature_names)}")

        # Step 3: Train NBA Model
        print("\n🤖 Step 3: Model Training")
        print("-" * 70)

        nba_model = NextBestActionModel(model_path="./models")
        nba_model.feature_names = feature_names

        # Train with hyperparameter optimization
        nba_model.train(
            X_train, y_train,
            X_val, y_val,
            hyperparameter_search=True,
            n_iter=20
        )

        # Step 4: Evaluate Model
        print("\n📈 Step 4: Model Evaluation")
        print("-" * 70)

        metrics = nba_model.evaluate(X_test, y_test, detailed=True)

        # Check if model meets success criteria
        success = True
        requirements = [
            ("Accuracy ≥ 85%", metrics['accuracy'] >= 0.85),
            ("F1 Score ≥ 0.80", metrics['f1_score'] >= 0.80),
        ]

        print("\n📋 Success Criteria Check:")
        print("-" * 70)
        for requirement, passed in requirements:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}  {requirement}")
            if not passed:
                success = False

        # Step 5: Feature Importance Analysis
        print("\n🔍 Step 5: Feature Importance")
        print("-" * 70)

        importance_df = nba_model.get_feature_importance(
            feature_names=feature_names,
            top_n=15
        )

        print("\nTop 15 Most Important Features:")
        for idx, row in importance_df.iterrows():
            print(f"  {row['feature']:.<50} {row['importance']:.6f}")

        # Step 6: Save Model
        print("\n💾 Step 6: Saving Model")
        print("-" * 70)

        model_file = nba_model.save(version="1.0")
        logger.info(f"✅ Model saved to {model_file}")

        # Save pipeline for later use
        import joblib
        pipeline_file = Path("./models/feature_pipeline_v1.0.joblib")
        joblib.dump(pipeline, pipeline_file, protocol=5)
        logger.info(f"✅ Feature pipeline saved to {pipeline_file}")

        # Save processed data for analysis
        data_dir = Path("./data/processed")
        data_dir.mkdir(exist_ok=True, parents=True)

        train_df.to_parquet(data_dir / "train.parquet", index=False)
        val_df.to_parquet(data_dir / "val.parquet", index=False)
        test_df.to_parquet(data_dir / "test.parquet", index=False)

        logger.info(f"✅ Processed data saved to {data_dir}/")

        # Final Summary
        print("\n" + "=" * 70)
        if success:
            print("✅ TRAINING COMPLETE - ALL SUCCESS CRITERIA MET")
        else:
            print("⚠️  TRAINING COMPLETE - SOME CRITERIA NOT MET")
        print("=" * 70)

        print(f"\nModel Performance:")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1_score']:.4f}")

        print(f"\nArtifacts Saved:")
        print(f"  Model:    {model_file}")
        print(f"  Pipeline: {pipeline_file}")
        print(f"  Data:     {data_dir}/")

        print(f"\nNext Steps:")
        print(f"  1. Deploy model to staging environment")
        print(f"  2. Test API endpoints with model")
        print(f"  3. Configure n8n workflows")
        print(f"  4. Build Streamlit dashboard")

        return 0 if success else 1

    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
