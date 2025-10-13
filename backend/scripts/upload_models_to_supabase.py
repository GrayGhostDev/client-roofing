#!/usr/bin/env python3
"""
Upload ML models to Supabase Storage for Railway deployment.

This script uploads trained model files from the local models/ directory
to Supabase Storage, where they can be downloaded by Railway at startup.

Usage:
    python scripts/upload_models_to_supabase.py

Environment variables required:
    SUPABASE_URL: Your Supabase project URL
    SUPABASE_SERVICE_KEY: Your Supabase service role key (has admin access)
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
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
MODELS_DIR = Path(__file__).parent.parent / 'models'
STORAGE_BUCKET = 'ml-models'

# Model files to upload
MODEL_FILES = [
    {
        'local': 'nba_model_v1.0.joblib',
        'remote': 'production/nba_model_v1.0.joblib',
        'content_type': 'application/octet-stream'
    },
    {
        'local': 'nba_model_v1.0_metadata.json',
        'remote': 'production/nba_model_v1.0_metadata.json',
        'content_type': 'application/json'
    }
]


def create_bucket_if_not_exists(supabase: Client, bucket_name: str):
    """Create storage bucket if it doesn't exist."""
    try:
        # Try to get bucket info
        supabase.storage.get_bucket(bucket_name)
        logger.info(f"✅ Bucket '{bucket_name}' already exists")
        return True
    except Exception as e:
        # Bucket doesn't exist, create it
        logger.info(f"Creating bucket '{bucket_name}'...")
        try:
            supabase.storage.create_bucket(
                bucket_name,
                options={
                    'public': False,  # Private bucket for security
                    'file_size_limit': 104857600,  # 100MB max file size
                    'allowed_mime_types': [
                        'application/octet-stream',
                        'application/json'
                    ]
                }
            )
            logger.info(f"✅ Created bucket '{bucket_name}'")
            return True
        except Exception as create_error:
            logger.error(f"❌ Failed to create bucket: {create_error}")
            return False


def upload_model_file(
    supabase: Client,
    local_path: Path,
    remote_path: str,
    content_type: str
):
    """Upload a single model file to Supabase Storage."""
    try:
        # Check if local file exists
        if not local_path.exists():
            logger.error(f"❌ Local file not found: {local_path}")
            return False

        # Get file size
        file_size = local_path.stat().st_size
        logger.info(f"Uploading {local_path.name} ({file_size:,} bytes)...")

        # Read file content
        with open(local_path, 'rb') as f:
            file_content = f.read()

        # Upload to Supabase Storage
        supabase.storage.from_(STORAGE_BUCKET).upload(
            remote_path,
            file_content,
            {
                'content-type': content_type,
                'upsert': 'true'  # Overwrite if exists
            }
        )

        # Get public URL (even though bucket is private, we'll use signed URLs)
        logger.info(f"✅ Uploaded {remote_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to upload {local_path.name}: {e}")
        return False


def verify_upload(supabase: Client, remote_path: str, expected_size: int):
    """Verify uploaded file exists and has correct size."""
    try:
        # List files in bucket
        files = supabase.storage.from_(STORAGE_BUCKET).list('production')

        # Find our file
        filename = remote_path.split('/')[-1]
        file_info = next((f for f in files if f['name'] == filename), None)

        if not file_info:
            logger.error(f"❌ File not found in storage: {remote_path}")
            return False

        # Check size matches
        actual_size = file_info.get('metadata', {}).get('size', 0)
        if actual_size != expected_size:
            logger.warning(
                f"⚠️  Size mismatch for {filename}: "
                f"expected {expected_size:,} bytes, got {actual_size:,} bytes"
            )
            return False

        logger.info(f"✅ Verified {filename} ({actual_size:,} bytes)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to verify {remote_path}: {e}")
        return False


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("ML Model Upload to Supabase Storage")
    logger.info("=" * 60)

    # Validate environment
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("❌ Missing required environment variables:")
        logger.error("   SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    # Validate models directory
    if not MODELS_DIR.exists():
        logger.error(f"❌ Models directory not found: {MODELS_DIR}")
        logger.error("   Please train models first using Week 8 scripts")
        sys.exit(1)

    # Initialize Supabase client
    logger.info(f"Connecting to Supabase: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Create bucket if needed
    if not create_bucket_if_not_exists(supabase, STORAGE_BUCKET):
        logger.error("❌ Failed to create/access storage bucket")
        sys.exit(1)

    # Upload all model files
    upload_success = True
    uploaded_files = []

    for model_file in MODEL_FILES:
        local_path = MODELS_DIR / model_file['local']
        remote_path = model_file['remote']
        content_type = model_file['content_type']

        # Upload file
        success = upload_model_file(
            supabase,
            local_path,
            remote_path,
            content_type
        )

        if success:
            # Verify upload
            file_size = local_path.stat().st_size
            verified = verify_upload(supabase, remote_path, file_size)
            if verified:
                uploaded_files.append({
                    'name': model_file['local'],
                    'size': file_size,
                    'remote': remote_path
                })
            else:
                upload_success = False
        else:
            upload_success = False

    # Print summary
    logger.info("=" * 60)
    if upload_success:
        logger.info("✅ Upload Summary: SUCCESS")
        logger.info(f"   Uploaded {len(uploaded_files)} files to '{STORAGE_BUCKET}'")

        total_size = sum(f['size'] for f in uploaded_files)
        logger.info(f"   Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")

        logger.info("\n📋 Uploaded Files:")
        for f in uploaded_files:
            logger.info(f"   - {f['name']} → {f['remote']}")

        logger.info("\n🚀 Next Steps:")
        logger.info("   1. Set SUPABASE_URL and SUPABASE_KEY in Railway")
        logger.info("   2. Deploy to Railway: railway up")
        logger.info("   3. Models will auto-download at startup")

        sys.exit(0)
    else:
        logger.error("❌ Upload Summary: FAILED")
        logger.error("   Some files failed to upload")
        logger.error("   Check errors above and retry")
        sys.exit(1)


if __name__ == "__main__":
    main()
