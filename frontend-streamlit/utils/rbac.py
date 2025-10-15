"""
Role-Based Access Control (RBAC) for iSwitch Roofs CRM
Production-ready role and permission management
"""

import streamlit as st
from typing import List
from functools import wraps
from utils.supabase_auth import get_auth_client


# Role definitions
class Roles:
    """User role constants"""
    ADMIN = "Admin"
    MANAGER = "Manager"
    SALES_REP = "Sales Representative"
    OTHER = "Other"


# Permission mappings
ROLE_PERMISSIONS = {
    Roles.ADMIN: [
        "view_dashboard",
        "manage_leads",
        "manage_customers",
        "manage_projects",
        "view_analytics",
        "manage_team",
        "manage_users",
        "view_reports",
        "export_data",
        "system_settings",
        "view_all_data",
        "delete_records",
    ],
    Roles.MANAGER: [
        "view_dashboard",
        "manage_leads",
        "manage_customers",
        "manage_projects",
        "view_analytics",
        "view_reports",
        "export_data",
        "view_team_data",
    ],
    Roles.SALES_REP: [
        "view_dashboard",
        "manage_leads",
        "view_customers",
        "view_projects",
        "view_own_data",
    ],
    Roles.OTHER: [
        "view_dashboard",
        "view_own_data",
    ],
}


def get_user_role() -> str:
    """
    Get the role of the currently authenticated user

    Returns:
        str: User role (Admin, Manager, Sales Representative, Other)
    """
    auth = get_auth_client()
    metadata = auth.get_user_metadata()
    return metadata.get('role', Roles.OTHER)


def get_user_permissions() -> List[str]:
    """
    Get list of permissions for the current user based on their role

    Returns:
        List[str]: List of permission strings
    """
    role = get_user_role()
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(permission: str) -> bool:
    """
    Check if current user has a specific permission

    Args:
        permission: Permission string to check

    Returns:
        bool: True if user has permission
    """
    permissions = get_user_permissions()
    return permission in permissions


def has_role(required_role: str) -> bool:
    """
    Check if current user has a specific role

    Args:
        required_role: Role to check for

    Returns:
        bool: True if user has the role
    """
    user_role = get_user_role()
    return user_role == required_role


def has_any_role(required_roles: List[str]) -> bool:
    """
    Check if current user has any of the specified roles

    Args:
        required_roles: List of roles to check

    Returns:
        bool: True if user has any of the roles
    """
    user_role = get_user_role()
    return user_role in required_roles


def is_admin() -> bool:
    """Check if current user is an admin"""
    return has_role(Roles.ADMIN)


def is_manager() -> bool:
    """Check if current user is a manager"""
    return has_role(Roles.MANAGER)


def is_manager_or_admin() -> bool:
    """Check if current user is a manager or admin"""
    return has_any_role([Roles.ADMIN, Roles.MANAGER])


def require_permission(permission: str):
    """
    Decorator to require a specific permission for a function/page
    Production use: Add to top of page modules to enforce access control

    Args:
        permission: Permission string required
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_permission(permission):
                st.error("⛔ Access Denied: You don't have permission to access this feature")
                st.info(f"Required permission: `{permission}`")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: str):
    """
    Decorator to require a specific role for a function/page
    Production use: Restrict entire pages to specific roles

    Args:
        required_role: Role string required
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_role(required_role):
                user_role = get_user_role()
                st.error(f"⛔ Access Denied: This page requires {required_role} role")
                st.info(f"Your role: `{user_role}`")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(required_roles: List[str]):
    """
    Decorator to require any of specified roles for a function/page
    Production use: Allow multiple roles to access a page

    Args:
        required_roles: List of acceptable roles
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_any_role(required_roles):
                user_role = get_user_role()
                st.error(f"⛔ Access Denied: This page requires one of these roles: {', '.join(required_roles)}")
                st.info(f"Your role: `{user_role}`")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def show_role_badge():
    """
    Display a role badge for the current user in the UI
    """
    role = get_user_role()

    # Color mapping for roles
    role_colors = {
        Roles.ADMIN: "#dc3545",  # Red
        Roles.MANAGER: "#fd7e14",  # Orange
        Roles.SALES_REP: "#28a745",  # Green
        Roles.OTHER: "#6c757d",  # Gray
    }

    color = role_colors.get(role, "#6c757d")

    st.markdown(f"""
        <div style="
            display: inline-block;
            background: {color};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 8px;
        ">
            {role}
        </div>
    """, unsafe_allow_html=True)


def show_permission_info():
    """
    Display current user's permissions (for debugging/admin)
    """
    if not is_admin():
        return

    with st.expander("🔐 Your Permissions (Admin Only)"):
        role = get_user_role()
        permissions = get_user_permissions()

        st.write(f"**Role:** {role}")
        st.write(f"**Permissions ({len(permissions)}):**")

        cols = st.columns(2)
        for i, perm in enumerate(sorted(permissions)):
            with cols[i % 2]:
                st.write(f"✅ {perm}")


def filter_navigation_by_role():
    """
    Return navigation pages filtered by user role
    Production use: Dynamically filter nav based on user permissions

    Returns:
        List[str]: List of accessible page names
    """
    permissions = get_user_permissions()

    # Production page permissions mapping
    page_permissions = {
        "Dashboard": "view_dashboard",
        "Leads": "manage_leads",
        "Customers": "manage_customers",
        "Projects": "manage_projects",
        "Analytics": "view_analytics",
        "Reports": "view_reports",
        "Team": "manage_team",
        "Settings": "system_settings",
    }

    # Filter pages based on current user permissions
    accessible_pages = []
    for page, required_perm in page_permissions.items():
        if required_perm in permissions:
            accessible_pages.append(page)

    return accessible_pages


def can_view_user_data(target_user_id: str) -> bool:
    """
    Check if current user can view another user's data

    Args:
        target_user_id: User ID to check access for

    Returns:
        bool: True if user can view the data
    """
    auth = get_auth_client()
    current_user = auth.get_current_user()

    if not current_user:
        return False

    # Admins and managers can view all data
    if has_any_role([Roles.ADMIN, Roles.MANAGER]):
        return True

    # Users can view their own data
    current_user_id = st.session_state.get('user_id')
    if current_user_id == target_user_id:
        return True

    return False


def can_edit_user_data(target_user_id: str) -> bool:
    """
    Check if current user can edit another user's data

    Args:
        target_user_id: User ID to check edit access for

    Returns:
        bool: True if user can edit the data
    """
    auth = get_auth_client()
    current_user = auth.get_current_user()

    if not current_user:
        return False

    # Admins can edit all data
    if is_admin():
        return True

    # Managers can edit their team's data
    # Production: Implement team assignment lookup from database
    if is_manager():
        return False  # Requires team membership validation

    # Users can edit their own data
    current_user_id = st.session_state.get('user_id')
    if current_user_id == target_user_id:
        return True

    return False


def get_role_description(role: str) -> str:
    """
    Get a description of what a role can do

    Args:
        role: Role name

    Returns:
        str: Description of role capabilities
    """
    descriptions = {
        Roles.ADMIN: "Full system access including user management and settings",
        Roles.MANAGER: "Access to team data, analytics, and reports",
        Roles.SALES_REP: "Access to leads, customers, and own sales data",
        Roles.OTHER: "Basic dashboard access and personal data",
    }
    return descriptions.get(role, "Custom role with limited access")
