#!/usr/bin/env python3
"""Check Python syntax of component files."""

import ast
import os

def check_syntax():
    """Check syntax of all component files."""
    files_to_check = [
        'frontend_reflex/components/analytics.py',
        'frontend_reflex/components/projects.py',
        'frontend_reflex/components/settings.py',
        'frontend_reflex/components/leads.py',
        'frontend_reflex/components/customers.py',
        'frontend_reflex/components/kanban/kanban_board.py',
        'frontend_reflex/pages/appointments.py'
    ]

    print("Checking Python syntax of component files...")
    all_good = True

    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                ast.parse(content)
                print(f'✓ {file_path}: Syntax OK')
            except SyntaxError as e:
                print(f'❌ {file_path}: Syntax Error - {e}')
                all_good = False
        else:
            print(f'⚠️  {file_path}: File not found')
            all_good = False

    if all_good:
        print("\n✅ All files have valid Python syntax!")
    else:
        print("\n❌ Some files have syntax errors")

    return all_good

def extract_functions():
    """Extract function names from component files."""
    files_and_functions = {
        'frontend_reflex/components/analytics.py': ['analytics_page', 'analytics_dashboard'],
        'frontend_reflex/components/projects.py': ['projects_list_page', 'projects_page', 'project_timeline_page'],
        'frontend_reflex/components/settings.py': ['settings_page', 'settings_dashboard'],
        'frontend_reflex/components/leads.py': ['leads_list_page', 'leads_page'],
        'frontend_reflex/components/customers.py': ['customers_list_page', 'customers_page'],
        'frontend_reflex/components/kanban/kanban_board.py': ['kanban_board', 'kanban_board_page'],
        'frontend_reflex/pages/appointments.py': ['appointments_page']
    }

    print("\nChecking function definitions...")

    for file_path, expected_functions in files_and_functions.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()

            print(f"\n📁 {file_path}:")
            for func_name in expected_functions:
                if f"def {func_name}(" in content:
                    print(f"  ✓ {func_name}")
                elif f"{func_name} =" in content:
                    print(f"  ✓ {func_name} (alias)")
                else:
                    print(f"  ❌ {func_name} - Missing")

if __name__ == "__main__":
    check_syntax()
    extract_functions()