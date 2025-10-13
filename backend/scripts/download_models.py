#!/usr/bin/env python3
"""
Download ML models from Supabase Storage at Railway startup.

This script runs before the FastAPI server starts to ensure models
are available for predictions.
"""

import os
import sys
import logging
from pathlib import Path
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
MODELS_DIR = Path('/app/models')
STORAGE_BUCKET = 'ml-models'

# Model files to download
MODEL_FILES = [
    {
        'remote': 'production/nba_model_v1.0.joblib',
        'local': 'nba_model_v1.0.joblib',
        'required': True
    },
    {
        'remote': 'production/nba_model_v1.0_metadata.json',
        'local': 'nba_model_v1.0_metadata.json',
        'required': True
    }
]


def validate_environment():
    """Validate required environment variables."""
    if not SUPABASE_URL:
        logger.error("SUPABASE_URL environment variable is not set")
        return False

    if not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_SERVICE_KEY or SUPABASE_KEY environment variable is not set")
        return False

    return True


def create_models_directory():
    """Create models directory if it doesn't exist."""
    try:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Models directory ready: {MODELS_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create models directory: {e}")
        return False


def download_model_file(supabase: Client, remote_path: str, local_path: Path):
    """
    Download a single model file from Supabase Storage.

    Args:
        supabase: Supabase client instance
        remote_path: Path in Supabase Storage
        local_path: Local file path to save

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading {remote_path}...")

        # Download file from Supabase Storage
        data = supabase.storage.from_(STORAGE_BUCKET).download(remote_path)

        # Write to local file
        with open(local_path, 'wb') as f:
            f.write(data)

        # Verify file size
        file_size = local_path.stat().st_size
        logger.info(f"✅ Downloaded {remote_path} ({file_size:,} bytes)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to download {remote_path}: {e}")
        return False


def verify_models():
    """Verify that all required models exist and are valid."""
    all_valid = True

    for model_file in MODEL_FILES:
        local_path = MODELS_DIR / model_file['local']

        if not local_path.exists():
            logger.error(f"❌ Model file missing: {local_path}")
            all_valid = False
            continue

        file_size = local_path.stat().st_size
        if file_size == 0:
            logger.error(f"❌ Model file is empty: {local_path}")
            all_valid = False
            continue

        logger.info(f"✅ Verified: {model_file['local']} ({file_size:,} bytes)")

    return all_valid


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Starting model download process...")
    logger.info("=" * 60)

    # Step 1: Validate environment
    if not validate_environment():
        logger.error("Environment validation failed")
        sys.exit(1)

    # Step 2: Create models directory
    if not create_models_directory():
        logger.error("Failed to create models directory")
        sys.exit(1)

    # Step 3: Initialize Supabase client
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ Supabase client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        sys.exit(1)

    # Step 4: Download all model files
    download_success = True
    for model_file in MODEL_FILES:
        remote_path = model_file['remote']
        local_path = MODELS_DIR / model_file['local']

        # Skip if file already exists (for faster restarts)
        if local_path.exists() and local_path.stat().st_size > 0:
            logger.info(f"⏭️  Skipping {model_file['local']} (already exists)")
            continue

        success = download_model_file(supabase, remote_path, local_path)

        if not success and model_file['required']:
            download_success = False

    # Step 5: Verify all models
    if download_success and verify_models():
        logger.info("=" * 60)
        logger.info("✅ All models downloaded and verified successfully!")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("❌ Model download failed!")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
