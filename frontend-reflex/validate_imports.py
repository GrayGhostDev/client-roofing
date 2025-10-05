#!/usr/bin/env python3
"""Validation script to test all component imports before enabling routes."""

def test_imports():
    """Test all component imports to ensure they work correctly."""
    errors = []

    try:
        print("Testing kanban imports...")
        from frontend_reflex.components.kanban import kanban_board_page
        print("✓ kanban_board_page imported successfully")
    except ImportError as e:
        errors.append(f"❌ kanban_board_page: {e}")

    try:
        print("Testing leads imports...")
        from frontend_reflex.components.leads import leads_list_page, leads_page
        print("✓ leads_list_page and leads_page imported successfully")
    except ImportError as e:
        errors.append(f"❌ leads imports: {e}")

    try:
        print("Testing customers imports...")
        from frontend_reflex.components.customers import customers_list_page, customers_page
        print("✓ customers_list_page and customers_page imported successfully")
    except ImportError as e:
        errors.append(f"❌ customers imports: {e}")

    try:
        print("Testing projects imports...")
        from frontend_reflex.components.projects import projects_list_page, project_timeline_page, projects_page
        print("✓ projects_list_page, project_timeline_page, and projects_page imported successfully")
    except ImportError as e:
        errors.append(f"❌ projects imports: {e}")

    try:
        print("Testing analytics imports...")
        from frontend_reflex.components.analytics import analytics_page, analytics_dashboard
        print("✓ analytics_page and analytics_dashboard imported successfully")
    except ImportError as e:
        errors.append(f"❌ analytics imports: {e}")

    try:
        print("Testing settings imports...")
        from frontend_reflex.components.settings import settings_page, settings_dashboard
        print("✓ settings_page and settings_dashboard imported successfully")
    except ImportError as e:
        errors.append(f"❌ settings imports: {e}")

    try:
        print("Testing appointments imports...")
        from frontend_reflex.pages.appointments import appointments_page
        print("✓ appointments_page imported successfully")
    except ImportError as e:
        errors.append(f"❌ appointments_page: {e}")

    if errors:
        print("\n❌ IMPORT ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ ALL IMPORTS SUCCESSFUL!")
        print("\nAvailable functions for main app:")
        print("  - kanban_board_page")
        print("  - leads_list_page (alias: leads_page)")
        print("  - customers_list_page (alias: customers_page)")
        print("  - projects_list_page (alias: projects_page)")
        print("  - project_timeline_page")
        print("  - analytics_page (alias: analytics_dashboard)")
        print("  - settings_page (alias: settings_dashboard)")
        print("  - appointments_page")
        return True

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 Ready to enable routes in main app!")
    else:
        print("\n⚠️  Fix import errors before enabling routes.")