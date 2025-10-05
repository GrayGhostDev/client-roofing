"""Team management component - Complete team administration interface."""

import reflex as rx
from .settings_state import settings_state, TeamMember


def team_stats_cards() -> rx.Component:
    """Team statistics overview cards."""
    return rx.grid(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("users", size=20, color="blue"),
                    rx.text("Total Members", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                rx.text(str(len(settings_state.team_members)), size="6", weight="bold"),
                spacing="1"
            ),
            padding="4"
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("user-check", size=20, color="green"),
                    rx.text("Active", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                rx.text(
                    str(len([m for m in settings_state.team_members if m.status == "Active"])),
                    size="6",
                    weight="bold"
                ),
                spacing="1"
            ),
            padding="4"
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("trophy", size=20, color="amber"),
                    rx.text("Top Performer", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                rx.text("Emily Chen", size="3", weight="bold"),
                rx.text("96.5% score", size="1", color="gray"),
                spacing="1"
            ),
            padding="4"
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("dollar-sign", size=20, color="green"),
                    rx.text("Total Sales", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                rx.text("$1.46M", size="6", weight="bold"),
                spacing="1"
            ),
            padding="4"
        ),
        columns="4",
        spacing="4",
        width="100%"
    )


def team_filters() -> rx.Component:
    """Team member filtering controls."""
    return rx.hstack(
        # Search
        rx.input(
            placeholder="Search team members...",
            value=settings_state.search_query,
            width="300px",
            on_change=lambda val: None  # Handle search
        ),

        # Role filter
        rx.select.root(
            rx.select.trigger(
                rx.select.value(placeholder="All Roles"),
                width="150px"
            ),
            rx.select.content(
                rx.select.item("All Roles", value="all"),
                rx.select.item("Admin", value="Admin"),
                rx.select.item("Manager", value="Manager"),
                rx.select.item("Sales", value="Sales"),
                rx.select.item("Tech", value="Tech")
            )
        ),

        # Status filter
        rx.select.root(
            rx.select.trigger(
                rx.select.value(placeholder="All Status"),
                width="150px"
            ),
            rx.select.content(
                rx.select.item("All Status", value="all"),
                rx.select.item("Active", value="Active"),
                rx.select.item("Inactive", value="Inactive"),
                rx.select.item("Pending", value="Pending")
            )
        ),

        rx.spacer(),

        # Add member button
        rx.button(
            rx.hstack(
                rx.icon("plus", size=16),
                rx.text("Add Member"),
                spacing="2"
            ),
            color_scheme="blue",
            on_click=lambda: setattr(settings_state, 'show_add_member_modal', True)
        ),

        spacing="3",
        width="100%",
        align="center"
    )


def team_member_card(member: TeamMember) -> rx.Component:
    """Individual team member card."""
    return rx.card(
        rx.vstack(
            # Header with avatar and basic info
            rx.hstack(
                rx.avatar(
                    src=member.avatar_url,
                    fallback=f"{member.first_name[:1]}{member.last_name[:1]}",
                    size="5"
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(f"{member.first_name} {member.last_name}", size="3", weight="bold"),
                        rx.badge(
                            member.status,
                            color_scheme="green" if member.status == "Active" else "gray"
                        ),
                        spacing="2",
                        align="center"
                    ),
                    rx.hstack(
                        rx.badge(member.role, variant="outline"),
                        rx.text(member.territory, size="2", color="gray"),
                        spacing="2",
                        align="center"
                    ),
                    spacing="1",
                    align="start"
                ),
                rx.spacer(),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(
                            rx.icon("more-horizontal", size=16),
                            variant="ghost",
                            size="2"
                        )
                    ),
                    rx.menu.content(
                        rx.menu.item("View Profile", on_click=lambda: None),
                        rx.menu.item("Edit", on_click=lambda: None),
                        rx.menu.separator(),
                        rx.menu.item("Deactivate", color="red", on_click=lambda: None)
                    )
                ),
                align="center",
                width="100%"
            ),

            # Contact information
            rx.vstack(
                rx.hstack(
                    rx.icon("mail", size=14, color="gray"),
                    rx.text(member.email, size="2"),
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("phone", size=14, color="gray"),
                    rx.text(member.phone, size="2"),
                    spacing="2"
                ),
                spacing="2",
                align="start",
                width="100%"
            ),

            # Performance metrics (for sales roles)
            rx.cond(
                member.role == "Sales",
                rx.vstack(
                    rx.text("Performance", size="2", weight="medium", color="gray"),
                    rx.grid(
                        rx.vstack(
                            rx.text("Score", size="1", color="gray"),
                            rx.text(f"{member.performance_score:.1f}%", size="2", weight="bold"),
                            spacing="1"
                        ),
                        rx.vstack(
                            rx.text("Leads", size="1", color="gray"),
                            rx.text(str(member.total_leads), size="2", weight="bold"),
                            spacing="1"
                        ),
                        rx.vstack(
                            rx.text("Sales", size="1", color="gray"),
                            rx.text(f"${member.total_sales/1000:.0f}K", size="2", weight="bold"),
                            spacing="1"
                        ),
                        rx.vstack(
                            rx.text("Conv.", size="1", color="gray"),
                            rx.text(f"{member.conversion_rate:.1f}%", size="2", weight="bold"),
                            spacing="1"
                        ),
                        columns="4",
                        spacing="3",
                        width="100%"
                    ),
                    spacing="2",
                    width="100%"
                ),
                rx.fragment()
            ),

            # Skills and certifications
            rx.vstack(
                rx.text("Skills & Certifications", size="2", weight="medium", color="gray"),
                rx.hstack(
                    *[
                        rx.badge(skill, variant="soft", size="1")
                        for skill in member.skills[:3]  # Show first 3 skills
                    ],
                    spacing="1",
                    wrap="wrap"
                ),
                rx.hstack(
                    *[
                        rx.badge(cert, variant="outline", size="1", color_scheme="blue")
                        for cert in member.certifications[:2]  # Show first 2 certifications
                    ],
                    spacing="1",
                    wrap="wrap"
                ),
                spacing="2",
                width="100%"
            ),

            # Last active
            rx.hstack(
                rx.icon("clock", size=14, color="gray"),
                rx.text(f"Last active: {member.last_active[:10] if member.last_active else 'Never'}", size="1", color="gray"),
                spacing="2"
            ),

            spacing="4",
            align="start",
            width="100%"
        ),
        padding="4",
        width="100%"
    )


def team_members_grid() -> rx.Component:
    """Grid of team member cards."""
    return rx.grid(
        *[
            team_member_card(member)
            for member in settings_state.team_members
        ],
        columns="3",
        spacing="4",
        width="100%"
    )


def add_member_modal() -> rx.Component:
    """Modal for adding new team members."""
    return rx.dialog.root(
        rx.dialog.trigger(rx.fragment()),
        rx.dialog.content(
            rx.dialog.title("Add New Team Member"),
            rx.dialog.description("Enter the details for the new team member."),

            rx.vstack(
                # Personal Information
                rx.text("Personal Information", size="3", weight="bold"),
                rx.hstack(
                    rx.vstack(
                        rx.text("First Name", size="2", weight="medium"),
                        rx.input(placeholder="First name", width="100%"),
                        spacing="1",
                        width="100%"
                    ),
                    rx.vstack(
                        rx.text("Last Name", size="2", weight="medium"),
                        rx.input(placeholder="Last name", width="100%"),
                        spacing="1",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),

                rx.hstack(
                    rx.vstack(
                        rx.text("Email", size="2", weight="medium"),
                        rx.input(placeholder="email@company.com", width="100%"),
                        spacing="1",
                        width="100%"
                    ),
                    rx.vstack(
                        rx.text("Phone", size="2", weight="medium"),
                        rx.input(placeholder="(248) 555-0123", width="100%"),
                        spacing="1",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),

                # Role and Territory
                rx.text("Role & Territory", size="3", weight="bold"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Role", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(
                                rx.select.value(placeholder="Select role"),
                                width="100%"
                            ),
                            rx.select.content(
                                rx.select.item("Admin", value="Admin"),
                                rx.select.item("Manager", value="Manager"),
                                rx.select.item("Sales", value="Sales"),
                                rx.select.item("Tech", value="Tech")
                            )
                        ),
                        spacing="1",
                        width="100%"
                    ),
                    rx.vstack(
                        rx.text("Territory", size="2", weight="medium"),
                        rx.input(placeholder="Service territory", width="100%"),
                        spacing="1",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),

                # Commission Settings
                rx.text("Commission Settings", size="3", weight="bold"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Commission Type", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(
                                rx.select.value(placeholder="Select type"),
                                width="100%"
                            ),
                            rx.select.content(
                                rx.select.item("Percentage", value="percentage"),
                                rx.select.item("Flat Rate", value="flat")
                            )
                        ),
                        spacing="1",
                        width="100%"
                    ),
                    rx.vstack(
                        rx.text("Commission Rate", size="2", weight="medium"),
                        rx.input(placeholder="5.5 or 500", width="100%"),
                        spacing="1",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),

                spacing="4",
                width="100%"
            ),

            rx.flex(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray")
                ),
                rx.dialog.close(
                    rx.button("Add Member", color_scheme="blue")
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
            max_width="600px"
        ),
        open=settings_state.show_add_member_modal,
        on_open_change=lambda open: setattr(settings_state, 'show_add_member_modal', open)
    )


def team_analytics_section() -> rx.Component:
    """Team analytics and performance overview."""
    return rx.vstack(
        rx.text("Team Analytics", size="4", weight="bold"),

        # Performance leaderboard
        rx.vstack(
            rx.text("Performance Leaderboard", size="3", weight="medium"),
            rx.vstack(
                *[
                    rx.hstack(
                        rx.text(f"#{i+1}", size="2", weight="bold", width="30px"),
                        rx.avatar(
                            src=member.avatar_url,
                            fallback=f"{member.first_name[:1]}{member.last_name[:1]}",
                            size="3"
                        ),
                        rx.vstack(
                            rx.text(f"{member.first_name} {member.last_name}", size="2", weight="medium"),
                            rx.text(f"{member.role} • {member.territory}", size="1", color="gray"),
                            spacing="0",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.text(f"{member.performance_score:.1f}%", size="2", weight="bold"),
                        align="center",
                        width="100%",
                        padding="3",
                        border_radius="6px",
                        border="1px solid",
                        border_color="gray.3"
                    )
                    for i, member in enumerate(sorted(settings_state.team_members, key=lambda m: m.performance_score, reverse=True)[:5])
                ],
                spacing="2",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        # Workload distribution
        rx.vstack(
            rx.text("Current Workload", size="3", weight="medium"),
            rx.text("Distribution of active leads and projects", size="2", color="gray"),
            rx.grid(
                *[
                    rx.card(
                        rx.vstack(
                            rx.text(f"{member.first_name} {member.last_name}", size="2", weight="medium"),
                            rx.text(f"{member.total_leads} leads", size="1", color="gray"),
                            rx.progress(
                                value=min(member.total_leads, 100),  # Cap at 100 for display
                                max=100,
                                width="100%"
                            ),
                            spacing="2"
                        ),
                        padding="3"
                    )
                    for member in settings_state.team_members if member.role == "Sales"
                ],
                columns="2",
                spacing="3",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def team_management_section() -> rx.Component:
    """Complete team management section."""
    return rx.vstack(
        # Statistics cards
        team_stats_cards(),

        rx.divider(),

        # Filters and controls
        team_filters(),

        rx.divider(),

        # Two-column layout
        rx.hstack(
            # Left side - Team members
            rx.vstack(
                rx.text("Team Members", size="4", weight="bold"),
                team_members_grid(),
                spacing="4",
                width="100%",
                flex="2"
            ),

            # Right side - Analytics
            team_analytics_section(),

            spacing="8",
            width="100%",
            align="start"
        ),

        # Modals
        add_member_modal(),

        spacing="6",
        width="100%"
    )


def team_management_page() -> rx.Component:
    """Team management page wrapper."""
    return rx.container(
        rx.vstack(
            rx.heading("Team Management", size="6", weight="bold"),
            rx.text("Manage your team members, roles, and performance", size="3", color="gray"),
            team_management_section(),
            spacing="6",
            align="stretch"
        ),
        max_width="1400px",
        padding="4"
    )