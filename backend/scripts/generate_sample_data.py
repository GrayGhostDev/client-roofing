#!/usr/bin/env python3
"""
Generate Sample Data Script
Populates database with realistic lead data for testing and demonstration
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.services.intelligence.live_data_collector import run_live_collection


async def main():
    """Generate sample data"""
    print("=" * 80)
    print("🎯 iSwitch Roofs - Sample Data Generator")
    print("=" * 80)
    print()

    # Get database session
    db = SessionLocal()

    try:
        # Generate 100 sample leads
        print("Starting lead generation...")
        print()

        results = await run_live_collection(db, count=100)

        print()
        print("=" * 80)
        print("✅ GENERATION COMPLETE")
        print("=" * 80)
        print()
        print(f"📊 Results:")
        print(f"   - Total Generated: {results['total']}")
        print(f"   - Successfully Ingested: {results['ingested']}")
        print(f"   - Duplicates Skipped: {results['skipped']}")
        print()

        if results.get('errors'):
            print("⚠️  Errors encountered:")
            for error in results['errors'][:5]:
                print(f"   - {error}")
            print()

        print("🎉 Sample data is now available in the CRM!")
        print()
        print("Next steps:")
        print("   1. Start the Streamlit dashboard: streamlit run Home.py")
        print("   2. Navigate to: Leads Dashboard")
        print("   3. View generated leads and analytics")
        print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
