"""
Project Service Layer
Version: 1.0.0

Business logic for project management including scheduling, progress tracking,
resource allocation, and profitability analysis.
"""

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.project_schemas import (
    ProjectCreate,
    ProjectStatus,
    ProjectType,
    ProjectUpdate,
)
from app.services.notification import notification_service
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project management operations."""

    def __init__(self):
        """Initialize Project Service."""
        self.supabase = None

    def _get_client(self):
        """Get Supabase client."""
        if not self.supabase:
            self.supabase = get_supabase_client()
        return self.supabase

    def create_project(
        self, project_data: ProjectCreate, created_by: str
    ) -> tuple[bool, dict | None, str | None]:
        """
        Create a new project.

        Args:
            project_data: Project creation data
            created_by: User creating the project

        Returns:
            Tuple of (success, project_dict, error_message)
        """
        try:
            client = self._get_client()

            # Prepare project data
            project_dict = project_data.model_dump()
            project_dict["id"] = str(uuid4())
            project_dict["created_by"] = created_by
            project_dict["created_at"] = datetime.utcnow().isoformat()
            project_dict["updated_at"] = datetime.utcnow().isoformat()

            # Calculate initial metrics
            if project_dict.get("estimated_value") and project_dict.get("materials_cost"):
                labor_cost = project_dict.get("labor_cost", 0)
                total_cost = project_dict["materials_cost"] + labor_cost
                project_dict["profit_margin"] = (
                    (project_dict["estimated_value"] - total_cost) / project_dict["estimated_value"]
                ) * 100

            # Insert project
            result = client.from_("projects").insert(project_dict).execute()

            if result.data:
                project = result.data[0]

                # Send notification
                notification_service.send_notification(
                    type="project_created",
                    data={
                        "project_id": project["id"],
                        "project_name": project["name"],
                        "customer_id": project["customer_id"],
                        "estimated_value": project.get("estimated_value"),
                        "status": project["status"],
                    },
                    recipient_id=project.get("assigned_to"),
                    priority="normal",
                )

                logger.info(f"Project created: {project['id']}")
                return True, project, None

            return False, None, "Failed to create project"

        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return False, None, str(e)

    def update_project(
        self, project_id: str, update_data: ProjectUpdate, updated_by: str
    ) -> tuple[bool, dict | None, str | None]:
        """
        Update an existing project.

        Args:
            project_id: Project ID
            update_data: Update data
            updated_by: User updating the project

        Returns:
            Tuple of (success, project_dict, error_message)
        """
        try:
            client = self._get_client()

            # Get current project
            current = client.from_("projects").select("*").eq("id", project_id).execute()
            if not current.data:
                return False, None, "Project not found"

            old_project = current.data[0]

            # Prepare update data
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            update_dict["updated_by"] = updated_by

            # Recalculate profit margin if costs change
            if (
                "materials_cost" in update_dict
                or "labor_cost" in update_dict
                or "actual_value" in update_dict
            ):
                materials = update_dict.get("materials_cost", old_project.get("materials_cost", 0))
                labor = update_dict.get("labor_cost", old_project.get("labor_cost", 0))
                value = update_dict.get("actual_value") or update_dict.get(
                    "estimated_value", old_project.get("estimated_value", 0)
                )

                if value > 0:
                    total_cost = materials + labor
                    update_dict["profit_margin"] = ((value - total_cost) / value) * 100

            # Update project
            result = client.from_("projects").update(update_dict).eq("id", project_id).execute()

            if result.data:
                project = result.data[0]

                # Check for status changes
                if old_project["status"] != project["status"]:
                    self._handle_status_change(project, old_project["status"], updated_by)

                logger.info(f"Project updated: {project_id}")
                return True, project, None

            return False, None, "Failed to update project"

        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            return False, None, str(e)

    def _handle_status_change(self, project: dict, old_status: str, updated_by: str):
        """
        Handle project status change notifications and updates.

        Args:
            project: Updated project
            old_status: Previous status
            updated_by: User who made the change
        """
        try:
            # Determine notification type based on status change
            if (
                project["status"] == ProjectStatus.IN_PROGRESS.value
                and old_status != ProjectStatus.IN_PROGRESS.value
            ):
                notification_type = "project_started"
            elif project["status"] == ProjectStatus.COMPLETED.value:
                notification_type = "project_completed"
            elif project["status"] == ProjectStatus.ON_HOLD.value:
                notification_type = "project_on_hold"
            elif project["status"] == ProjectStatus.CANCELLED.value:
                notification_type = "project_cancelled"
            else:
                notification_type = "project_updated"

            # Send notification
            notification_service.send_notification(
                type=notification_type,
                data={
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "old_status": old_status,
                    "new_status": project["status"],
                    "updated_by": updated_by,
                },
                recipient_id=project.get("assigned_to"),
                priority="high" if project["status"] == ProjectStatus.CANCELLED.value else "normal",
            )

        except Exception as e:
            logger.error(f"Error handling status change: {str(e)}")

    def get_project_timeline(self, project_id: str) -> dict | None:
        """
        Get project timeline and milestones.

        Args:
            project_id: Project ID

        Returns:
            Timeline data or None
        """
        try:
            client = self._get_client()

            # Get project
            result = client.from_("projects").select("*").eq("id", project_id).execute()
            if not result.data:
                return None

            project = result.data[0]

            # Calculate timeline
            timeline = {
                "project_id": project_id,
                "start_date": project.get("start_date"),
                "end_date": project.get("end_date"),
                "duration_days": None,
                "progress_percentage": 0,
                "is_delayed": False,
                "days_remaining": None,
                "milestones": [],
            }

            # Calculate duration and progress
            if project.get("start_date"):
                start = datetime.fromisoformat(project["start_date"])

                if project.get("end_date"):
                    end = datetime.fromisoformat(project["end_date"])
                    timeline["duration_days"] = (end - start).days

                    # Calculate progress
                    if project["status"] == ProjectStatus.COMPLETED.value:
                        timeline["progress_percentage"] = 100
                    elif project["status"] == ProjectStatus.IN_PROGRESS.value:
                        elapsed = (datetime.utcnow() - start).days
                        if timeline["duration_days"] > 0:
                            timeline["progress_percentage"] = min(
                                100, (elapsed / timeline["duration_days"]) * 100
                            )

                    # Check if delayed
                    if (
                        datetime.utcnow() > end
                        and project["status"] != ProjectStatus.COMPLETED.value
                    ):
                        timeline["is_delayed"] = True
                    else:
                        timeline["days_remaining"] = max(0, (end - datetime.utcnow()).days)

            # Add milestones based on project type
            if project["project_type"] == ProjectType.REPLACEMENT.value:
                timeline["milestones"] = [
                    {"name": "Initial Inspection", "target_days": 1, "completed": False},
                    {"name": "Material Ordering", "target_days": 2, "completed": False},
                    {"name": "Tear-off", "target_days": 3, "completed": False},
                    {"name": "Installation", "target_days": 5, "completed": False},
                    {"name": "Final Inspection", "target_days": 6, "completed": False},
                ]
            elif project["project_type"] == ProjectType.REPAIR.value:
                timeline["milestones"] = [
                    {"name": "Damage Assessment", "target_days": 1, "completed": False},
                    {"name": "Repair Work", "target_days": 2, "completed": False},
                    {"name": "Quality Check", "target_days": 3, "completed": False},
                ]

            return timeline

        except Exception as e:
            logger.error(f"Error getting project timeline: {str(e)}")
            return None

    def calculate_project_profitability(self, project_id: str) -> dict | None:
        """
        Calculate detailed project profitability metrics.

        Args:
            project_id: Project ID

        Returns:
            Profitability data or None
        """
        try:
            client = self._get_client()

            # Get project
            result = client.from_("projects").select("*").eq("id", project_id).execute()
            if not result.data:
                return None

            project = result.data[0]

            # Calculate profitability
            materials_cost = project.get("materials_cost", 0)
            labor_cost = project.get("labor_cost", 0)
            subcontractor_cost = project.get("subcontractor_cost", 0)
            permit_cost = project.get("permit_cost", 0)
            other_costs = project.get("other_costs", 0)

            total_cost = (
                materials_cost + labor_cost + subcontractor_cost + permit_cost + other_costs
            )

            # Use actual value if completed, otherwise estimated
            revenue = (
                project.get("actual_value")
                if project["status"] == ProjectStatus.COMPLETED.value
                else project.get("estimated_value", 0)
            )

            gross_profit = revenue - total_cost
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0

            # Calculate ROI
            roi = ((gross_profit / total_cost) * 100) if total_cost > 0 else 0

            profitability = {
                "project_id": project_id,
                "revenue": revenue,
                "costs": {
                    "materials": materials_cost,
                    "labor": labor_cost,
                    "subcontractor": subcontractor_cost,
                    "permits": permit_cost,
                    "other": other_costs,
                    "total": total_cost,
                },
                "gross_profit": gross_profit,
                "gross_margin_percentage": round(gross_margin, 2),
                "roi_percentage": round(roi, 2),
                "cost_breakdown": {
                    "materials_percentage": (
                        round((materials_cost / total_cost * 100), 2) if total_cost > 0 else 0
                    ),
                    "labor_percentage": (
                        round((labor_cost / total_cost * 100), 2) if total_cost > 0 else 0
                    ),
                    "other_percentage": (
                        round(
                            ((subcontractor_cost + permit_cost + other_costs) / total_cost * 100), 2
                        )
                        if total_cost > 0
                        else 0
                    ),
                },
                "profitability_status": (
                    "excellent"
                    if gross_margin > 40
                    else "good" if gross_margin > 25 else "fair" if gross_margin > 15 else "poor"
                ),
            }

            return profitability

        except Exception as e:
            logger.error(f"Error calculating profitability: {str(e)}")
            return None

    def get_project_resources(self, project_id: str) -> dict | None:
        """
        Get project resource allocation and requirements.

        Args:
            project_id: Project ID

        Returns:
            Resource data or None
        """
        try:
            client = self._get_client()

            # Get project
            project_result = client.from_("projects").select("*").eq("id", project_id).execute()
            if not project_result.data:
                return None

            project = project_result.data[0]

            # Get assigned team members
            team_result = (
                client.from_("project_team").select("*").eq("project_id", project_id).execute()
            )
            team_members = team_result.data if team_result.data else []

            # Get material requirements
            materials_result = (
                client.from_("project_materials").select("*").eq("project_id", project_id).execute()
            )
            materials = materials_result.data if materials_result.data else []

            # Get equipment requirements
            equipment_result = (
                client.from_("project_equipment").select("*").eq("project_id", project_id).execute()
            )
            equipment = equipment_result.data if equipment_result.data else []

            resources = {
                "project_id": project_id,
                "team": {
                    "assigned_to": project.get("assigned_to"),
                    "team_members": team_members,
                    "crew_size_required": self._estimate_crew_size(project),
                    "estimated_man_hours": self._estimate_man_hours(project),
                },
                "materials": {
                    "list": materials,
                    "total_cost": project.get("materials_cost", 0),
                    "ordered": (
                        len([m for m in materials if m.get("status") == "ordered"])
                        if materials
                        else 0
                    ),
                    "received": (
                        len([m for m in materials if m.get("status") == "received"])
                        if materials
                        else 0
                    ),
                },
                "equipment": {
                    "list": equipment,
                    "rental_cost": (
                        sum(e.get("rental_cost", 0) for e in equipment) if equipment else 0
                    ),
                },
                "subcontractors": {
                    "required": project.get("requires_subcontractor", False),
                    "cost": project.get("subcontractor_cost", 0),
                },
            }

            return resources

        except Exception as e:
            logger.error(f"Error getting project resources: {str(e)}")
            return None

    def _estimate_crew_size(self, project: dict) -> int:
        """
        Estimate required crew size based on project type and scope.

        Args:
            project: Project data

        Returns:
            Estimated crew size
        """
        if project["project_type"] == ProjectType.REPLACEMENT.value:
            # Base crew size for replacement
            if project.get("square_feet", 0) > 3000:
                return 6  # Large project
            elif project.get("square_feet", 0) > 1500:
                return 4  # Medium project
            else:
                return 3  # Small project
        elif project["project_type"] == ProjectType.REPAIR.value:
            return 2  # Repair crew
        else:
            return 3  # Default crew size

    def _estimate_man_hours(self, project: dict) -> int:
        """
        Estimate required man hours based on project scope.

        Args:
            project: Project data

        Returns:
            Estimated man hours
        """
        base_hours = 0

        if project["project_type"] == ProjectType.REPLACEMENT.value:
            # Estimate based on square footage
            sq_feet = project.get("square_feet", 2000)  # Default 2000 sq ft
            base_hours = sq_feet * 0.02  # 0.02 hours per sq ft
        elif project["project_type"] == ProjectType.REPAIR.value:
            base_hours = 8  # Standard repair time
        elif project["project_type"] == ProjectType.INSPECTION.value:
            base_hours = 2  # Inspection time
        else:
            base_hours = 16  # Default

        # Adjust for complexity
        if project.get("complexity") == "high":
            base_hours *= 1.5
        elif project.get("complexity") == "low":
            base_hours *= 0.75

        return int(base_hours)

    def schedule_project(
        self, project_id: str, start_date: datetime, crew_id: str | None = None
    ) -> tuple[bool, dict | None, str | None]:
        """
        Schedule a project with automatic end date calculation.

        Args:
            project_id: Project ID
            start_date: Proposed start date
            crew_id: Optional crew assignment

        Returns:
            Tuple of (success, schedule_data, error_message)
        """
        try:
            client = self._get_client()

            # Get project
            result = client.from_("projects").select("*").eq("id", project_id).execute()
            if not result.data:
                return False, None, "Project not found"

            project = result.data[0]

            # Calculate estimated duration
            duration_days = self._estimate_duration(project)
            end_date = start_date + timedelta(days=duration_days)

            # Check for conflicts if crew is specified
            if crew_id:
                conflicts = self._check_schedule_conflicts(crew_id, start_date, end_date)
                if conflicts:
                    return False, None, f"Schedule conflict: {conflicts}"

            # Update project schedule
            update_data = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "status": ProjectStatus.SCHEDULED.value,
                "assigned_crew": crew_id,
                "updated_at": datetime.utcnow().isoformat(),
            }

            update_result = (
                client.from_("projects").update(update_data).eq("id", project_id).execute()
            )

            if update_result.data:
                schedule_data = {
                    "project_id": project_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_days": duration_days,
                    "crew_id": crew_id,
                    "status": "scheduled",
                }

                # Send notification
                notification_service.send_notification(
                    type="project_scheduled",
                    data=schedule_data,
                    recipient_id=project.get("assigned_to"),
                    priority="normal",
                )

                logger.info(f"Project scheduled: {project_id}")
                return True, schedule_data, None

            return False, None, "Failed to schedule project"

        except Exception as e:
            logger.error(f"Error scheduling project: {str(e)}")
            return False, None, str(e)

    def _estimate_duration(self, project: dict) -> int:
        """
        Estimate project duration in days.

        Args:
            project: Project data

        Returns:
            Estimated duration in days
        """
        if project["project_type"] == ProjectType.REPLACEMENT.value:
            # Base duration for replacement
            sq_feet = project.get("square_feet", 2000)
            if sq_feet > 3000:
                base_days = 5  # Large project
            elif sq_feet > 1500:
                base_days = 3  # Medium project
            else:
                base_days = 2  # Small project
        elif project["project_type"] == ProjectType.REPAIR.value:
            base_days = 1  # Repair
        elif project["project_type"] == ProjectType.INSPECTION.value:
            base_days = 1  # Inspection
        else:
            base_days = 3  # Default

        # Add buffer for weather
        buffer_days = 1

        return base_days + buffer_days

    def _check_schedule_conflicts(
        self, crew_id: str, start_date: datetime, end_date: datetime
    ) -> str | None:
        """
        Check for scheduling conflicts.

        Args:
            crew_id: Crew ID
            start_date: Proposed start date
            end_date: Proposed end date

        Returns:
            Conflict description or None
        """
        try:
            client = self._get_client()

            # Query existing scheduled projects for the crew
            result = (
                client.from_("projects")
                .select("*")
                .eq("assigned_crew", crew_id)
                .gte("end_date", start_date.isoformat())
                .lte("start_date", end_date.isoformat())
                .execute()
            )

            if result.data:
                conflicts = [
                    f"Project {p['name']} ({p['start_date']} to {p['end_date']})"
                    for p in result.data
                ]
                return ", ".join(conflicts)

            return None

        except Exception as e:
            logger.error(f"Error checking schedule conflicts: {str(e)}")
            return None

    def get_project_documents(self, project_id: str) -> list[dict]:
        """
        Get all documents associated with a project.

        Args:
            project_id: Project ID

        Returns:
            List of documents
        """
        try:
            client = self._get_client()

            result = (
                client.from_("project_documents")
                .select("*")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting project documents: {str(e)}")
            return []

    def add_project_document(
        self, project_id: str, document_data: dict
    ) -> tuple[bool, dict | None, str | None]:
        """
        Add a document to a project.

        Args:
            project_id: Project ID
            document_data: Document information

        Returns:
            Tuple of (success, document, error_message)
        """
        try:
            client = self._get_client()

            # Verify project exists
            project_result = client.from_("projects").select("id").eq("id", project_id).execute()
            if not project_result.data:
                return False, None, "Project not found"

            # Add document
            document_data["id"] = str(uuid4())
            document_data["project_id"] = project_id
            document_data["created_at"] = datetime.utcnow().isoformat()

            result = client.from_("project_documents").insert(document_data).execute()

            if result.data:
                logger.info(f"Document added to project: {project_id}")
                return True, result.data[0], None

            return False, None, "Failed to add document"

        except Exception as e:
            logger.error(f"Error adding project document: {str(e)}")
            return False, None, str(e)


# Singleton instance
project_service = ProjectService()
