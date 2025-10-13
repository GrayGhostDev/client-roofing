"""
Interaction Service Layer
Version: 1.0.0

Business logic for customer interaction management including calls, emails,
meetings, follow-ups, and communication history tracking.
"""

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.interaction_schemas import (
    InteractionCreate,
    InteractionDirection,
    # InteractionStatus,  # TODO: This enum doesn't exist in the model - needs to be added
    InteractionUpdate,
)
from app.services.notification import notification_service
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class InteractionService:
    """Service for interaction management operations."""

    def __init__(self):
        """Initialize Interaction Service."""
        self.supabase = None

    def _get_client(self):
        """Get Supabase client."""
        if not self.supabase:
            self.supabase = get_supabase_client()
        return self.supabase

    def create_interaction(
        self, interaction_data: InteractionCreate, created_by: str
    ) -> tuple[bool, dict | None, str | None]:
        """
        Create a new interaction.

        Args:
            interaction_data: Interaction creation data
            created_by: User creating the interaction

        Returns:
            Tuple of (success, interaction_dict, error_message)
        """
        try:
            client = self._get_client()

            # Prepare interaction data
            interaction_dict = interaction_data.model_dump()
            interaction_dict["id"] = str(uuid4())
            interaction_dict["created_by"] = created_by
            interaction_dict["created_at"] = datetime.utcnow().isoformat()
            interaction_dict["updated_at"] = datetime.utcnow().isoformat()

            # Set default status if not provided
            # TODO: InteractionStatus enum doesn't exist - needs to be added to model
            # if "status" not in interaction_dict:
            #     interaction_dict["status"] = InteractionStatus.COMPLETED.value

            # Calculate duration if end_time provided
            if interaction_dict.get("start_time") and interaction_dict.get("end_time"):
                start = datetime.fromisoformat(interaction_dict["start_time"])
                end = datetime.fromisoformat(interaction_dict["end_time"])
                interaction_dict["duration_minutes"] = int((end - start).total_seconds() / 60)

            # Insert interaction
            result = client.from_("interactions").insert(interaction_dict).execute()

            if result.data:
                interaction = result.data[0]

                # Update customer last interaction
                self._update_customer_last_interaction(
                    interaction.get("customer_id"), interaction["id"]
                )

                # Handle follow-up if specified
                if interaction.get("follow_up_required") and interaction.get("follow_up_date"):
                    self._schedule_follow_up(interaction)

                # Send notification for important interactions
                if interaction.get("is_important"):
                    notification_service.send_notification(
                        type="important_interaction",
                        data={
                            "interaction_id": interaction["id"],
                            "customer_id": interaction.get("customer_id"),
                            "lead_id": interaction.get("lead_id"),
                            "type": interaction["interaction_type"],
                            "summary": interaction.get("summary", ""),
                        },
                        recipient_id=interaction.get("assigned_to"),
                        priority="high",
                    )

                logger.info(f"Interaction created: {interaction['id']}")
                return True, interaction, None

            return False, None, "Failed to create interaction"

        except Exception as e:
            logger.error(f"Error creating interaction: {str(e)}")
            return False, None, str(e)

    def update_interaction(
        self, interaction_id: str, update_data: InteractionUpdate, updated_by: str
    ) -> tuple[bool, dict | None, str | None]:
        """
        Update an existing interaction.

        Args:
            interaction_id: Interaction ID
            update_data: Update data
            updated_by: User updating the interaction

        Returns:
            Tuple of (success, interaction_dict, error_message)
        """
        try:
            client = self._get_client()

            # Get current interaction
            current = client.from_("interactions").select("*").eq("id", interaction_id).execute()
            if not current.data:
                return False, None, "Interaction not found"

            old_interaction = current.data[0]

            # Prepare update data
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            update_dict["updated_by"] = updated_by

            # Recalculate duration if times change
            if "start_time" in update_dict or "end_time" in update_dict:
                start = datetime.fromisoformat(
                    update_dict.get("start_time", old_interaction.get("start_time"))
                )
                end = datetime.fromisoformat(
                    update_dict.get("end_time", old_interaction.get("end_time"))
                )
                if start and end:
                    update_dict["duration_minutes"] = int((end - start).total_seconds() / 60)

            # Update interaction
            result = (
                client.from_("interactions").update(update_dict).eq("id", interaction_id).execute()
            )

            if result.data:
                interaction = result.data[0]

                # Handle follow-up changes
                if "follow_up_required" in update_dict or "follow_up_date" in update_dict:
                    if interaction.get("follow_up_required") and interaction.get("follow_up_date"):
                        self._schedule_follow_up(interaction)
                    else:
                        self._cancel_follow_up(interaction_id)

                logger.info(f"Interaction updated: {interaction_id}")
                return True, interaction, None

            return False, None, "Failed to update interaction"

        except Exception as e:
            logger.error(f"Error updating interaction: {str(e)}")
            return False, None, str(e)

    def _update_customer_last_interaction(self, customer_id: str | None, interaction_id: str):
        """
        Update customer's last interaction timestamp.

        Args:
            customer_id: Customer ID
            interaction_id: Interaction ID
        """
        if not customer_id:
            return

        try:
            client = self._get_client()
            client.from_("customers").update(
                {
                    "last_interaction": datetime.utcnow().isoformat(),
                    "last_interaction_id": interaction_id,
                }
            ).eq("id", customer_id).execute()

        except Exception as e:
            logger.error(f"Error updating customer last interaction: {str(e)}")

    def _schedule_follow_up(self, interaction: dict):
        """
        Schedule a follow-up for an interaction.

        Args:
            interaction: Interaction data
        """
        try:
            follow_up_date = datetime.fromisoformat(interaction["follow_up_date"])

            # Create a scheduled notification
            notification_service.schedule_notification(
                type="follow_up_reminder",
                data={
                    "interaction_id": interaction["id"],
                    "customer_id": interaction.get("customer_id"),
                    "original_interaction": interaction["interaction_type"],
                    "follow_up_notes": interaction.get("follow_up_notes", ""),
                },
                recipient_id=interaction.get("assigned_to"),
                send_at=follow_up_date - timedelta(hours=1),  # Remind 1 hour before
                priority="high",
            )

            logger.info(f"Follow-up scheduled for interaction: {interaction['id']}")

        except Exception as e:
            logger.error(f"Error scheduling follow-up: {str(e)}")

    def _cancel_follow_up(self, interaction_id: str):
        """
        Cancel a scheduled follow-up.

        Args:
            interaction_id: Interaction ID
        """
        try:
            # Cancel scheduled notifications for this interaction
            # This would need to be implemented in the notification service
            logger.info(f"Follow-up cancelled for interaction: {interaction_id}")

        except Exception as e:
            logger.error(f"Error cancelling follow-up: {str(e)}")

    def get_interaction_history(
        self, entity_id: str, entity_type: str = "customer", limit: int = 50
    ) -> list[dict]:
        """
        Get interaction history for a customer or lead.

        Args:
            entity_id: Customer or Lead ID
            entity_type: 'customer' or 'lead'
            limit: Maximum number of interactions to return

        Returns:
            List of interactions
        """
        try:
            client = self._get_client()

            if entity_type == "customer":
                query = client.from_("interactions").select("*").eq("customer_id", entity_id)
            else:
                query = client.from_("interactions").select("*").eq("lead_id", entity_id)

            result = query.order("interaction_time", desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting interaction history: {str(e)}")
            return []

    def get_communication_summary(self, entity_id: str, entity_type: str = "customer") -> dict:
        """
        Get communication summary for a customer or lead.

        Args:
            entity_id: Customer or Lead ID
            entity_type: 'customer' or 'lead'

        Returns:
            Communication summary
        """
        try:
            interactions = self.get_interaction_history(entity_id, entity_type, limit=100)

            if not interactions:
                return {
                    "total_interactions": 0,
                    "last_interaction": None,
                    "interaction_types": {},
                    "average_response_time": None,
                    "preferred_channel": None,
                }

            # Calculate summary statistics
            summary = {
                "total_interactions": len(interactions),
                "last_interaction": interactions[0] if interactions else None,
                "interaction_types": {},
                "total_duration_minutes": 0,
                "outbound_count": 0,
                "inbound_count": 0,
                "follow_ups_required": 0,
                "follow_ups_completed": 0,
            }

            # Count by type and direction
            for interaction in interactions:
                int_type = interaction.get("interaction_type", "unknown")
                summary["interaction_types"][int_type] = (
                    summary["interaction_types"].get(int_type, 0) + 1
                )

                if interaction.get("direction") == InteractionDirection.OUTBOUND.value:
                    summary["outbound_count"] += 1
                elif interaction.get("direction") == InteractionDirection.INBOUND.value:
                    summary["inbound_count"] += 1

                summary["total_duration_minutes"] += interaction.get("duration_minutes", 0)

                if interaction.get("follow_up_required"):
                    summary["follow_ups_required"] += 1
                    if interaction.get("follow_up_completed"):
                        summary["follow_ups_completed"] += 1

            # Determine preferred channel
            if summary["interaction_types"]:
                summary["preferred_channel"] = max(
                    summary["interaction_types"], key=summary["interaction_types"].get
                )

            # Calculate average response time for inbound interactions
            response_times = []
            for i in range(len(interactions) - 1):
                if interactions[i].get("direction") == InteractionDirection.INBOUND.value:
                    # Look for next outbound interaction
                    for j in range(i + 1, len(interactions)):
                        if interactions[j].get("direction") == InteractionDirection.OUTBOUND.value:
                            time1 = datetime.fromisoformat(interactions[i]["interaction_time"])
                            time2 = datetime.fromisoformat(interactions[j]["interaction_time"])
                            response_times.append((time1 - time2).total_seconds() / 3600)  # Hours
                            break

            summary["average_response_time_hours"] = (
                sum(response_times) / len(response_times) if response_times else None
            )

            return summary

        except Exception as e:
            logger.error(f"Error getting communication summary: {str(e)}")
            return {}

    def get_pending_follow_ups(
        self, assigned_to: str | None = None, days_ahead: int = 7
    ) -> list[dict]:
        """
        Get pending follow-ups for the next N days.

        Args:
            assigned_to: Filter by assigned user
            days_ahead: Number of days to look ahead

        Returns:
            List of interactions requiring follow-up
        """
        try:
            client = self._get_client()

            # Build query
            query = (
                client.from_("interactions")
                .select("*")
                .eq("follow_up_required", True)
                .eq("follow_up_completed", False)
            )

            if assigned_to:
                query = query.eq("assigned_to", assigned_to)

            # Get follow-ups due in the next N days
            end_date = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
            query = query.lte("follow_up_date", end_date)

            result = query.order("follow_up_date", desc=False).execute()
            follow_ups = result.data if result.data else []

            # Add customer/lead details
            for follow_up in follow_ups:
                if follow_up.get("customer_id"):
                    customer_result = (
                        client.from_("customers")
                        .select("first_name, last_name, email, phone")
                        .eq("id", follow_up["customer_id"])
                        .execute()
                    )
                    if customer_result.data:
                        follow_up["customer"] = customer_result.data[0]
                elif follow_up.get("lead_id"):
                    lead_result = (
                        client.from_("leads")
                        .select("first_name, last_name, email, phone")
                        .eq("id", follow_up["lead_id"])
                        .execute()
                    )
                    if lead_result.data:
                        follow_up["lead"] = lead_result.data[0]

            return follow_ups

        except Exception as e:
            logger.error(f"Error getting pending follow-ups: {str(e)}")
            return []

    def mark_follow_up_complete(
        self, interaction_id: str, notes: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Mark a follow-up as complete.

        Args:
            interaction_id: Interaction ID
            notes: Completion notes

        Returns:
            Tuple of (success, error_message)
        """
        try:
            client = self._get_client()

            update_data = {
                "follow_up_completed": True,
                "follow_up_completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            if notes:
                update_data["follow_up_completion_notes"] = notes

            result = (
                client.from_("interactions").update(update_data).eq("id", interaction_id).execute()
            )

            if result.data:
                logger.info(f"Follow-up completed: {interaction_id}")
                return True, None

            return False, "Failed to mark follow-up as complete"

        except Exception as e:
            logger.error(f"Error marking follow-up complete: {str(e)}")
            return False, str(e)

    def get_interaction_analytics(
        self, start_date: datetime, end_date: datetime, assigned_to: str | None = None
    ) -> dict:
        """
        Get interaction analytics for a date range.

        Args:
            start_date: Start date
            end_date: End date
            assigned_to: Filter by assigned user

        Returns:
            Analytics data
        """
        try:
            client = self._get_client()

            # Build query
            query = (
                client.from_("interactions")
                .select("*")
                .gte("interaction_time", start_date.isoformat())
                .lte("interaction_time", end_date.isoformat())
            )

            if assigned_to:
                query = query.eq("assigned_to", assigned_to)

            result = query.execute()
            interactions = result.data if result.data else []

            # Calculate analytics
            analytics = {
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "total_interactions": len(interactions),
                "interactions_by_type": {},
                "interactions_by_day": {},
                "interactions_by_hour": {},
                "average_duration_minutes": 0,
                "total_duration_hours": 0,
                "conversion_interactions": 0,
                "response_rate": 0,
                "follow_up_completion_rate": 0,
                "top_performers": {},
            }

            if not interactions:
                return analytics

            total_duration = 0
            follow_ups_required = 0
            follow_ups_completed = 0
            interactions_by_user = {}

            for interaction in interactions:
                # Count by type
                int_type = interaction.get("interaction_type", "unknown")
                analytics["interactions_by_type"][int_type] = (
                    analytics["interactions_by_type"].get(int_type, 0) + 1
                )

                # Count by day
                int_time = datetime.fromisoformat(interaction["interaction_time"])
                day = int_time.strftime("%Y-%m-%d")
                analytics["interactions_by_day"][day] = (
                    analytics["interactions_by_day"].get(day, 0) + 1
                )

                # Count by hour
                hour = int_time.hour
                analytics["interactions_by_hour"][hour] = (
                    analytics["interactions_by_hour"].get(hour, 0) + 1
                )

                # Sum duration
                total_duration += interaction.get("duration_minutes", 0)

                # Count conversions
                if interaction.get("resulted_in_conversion"):
                    analytics["conversion_interactions"] += 1

                # Count follow-ups
                if interaction.get("follow_up_required"):
                    follow_ups_required += 1
                    if interaction.get("follow_up_completed"):
                        follow_ups_completed += 1

                # Count by user
                user = interaction.get("created_by")
                if user:
                    if user not in interactions_by_user:
                        interactions_by_user[user] = {"count": 0, "duration": 0}
                    interactions_by_user[user]["count"] += 1
                    interactions_by_user[user]["duration"] += interaction.get("duration_minutes", 0)

            # Calculate averages
            analytics["average_duration_minutes"] = (
                total_duration / len(interactions) if interactions else 0
            )
            analytics["total_duration_hours"] = total_duration / 60

            # Calculate rates
            analytics["conversion_rate"] = (
                (analytics["conversion_interactions"] / len(interactions) * 100)
                if interactions
                else 0
            )
            analytics["follow_up_completion_rate"] = (
                (follow_ups_completed / follow_ups_required * 100)
                if follow_ups_required > 0
                else 100
            )

            # Get top performers
            top_users = sorted(
                interactions_by_user.items(), key=lambda x: x[1]["count"], reverse=True
            )[:5]
            analytics["top_performers"] = [
                {
                    "user_id": user,
                    "interaction_count": data["count"],
                    "total_duration_minutes": data["duration"],
                    "average_duration_minutes": (
                        data["duration"] / data["count"] if data["count"] > 0 else 0
                    ),
                }
                for user, data in top_users
            ]

            return analytics

        except Exception as e:
            logger.error(f"Error getting interaction analytics: {str(e)}")
            return {}

    def auto_log_interaction(
        self, interaction_type: str, entity_id: str, entity_type: str, details: dict
    ) -> tuple[bool, dict | None, str | None]:
        """
        Automatically log an interaction from system events.

        Args:
            interaction_type: Type of interaction
            entity_id: Customer or Lead ID
            entity_type: 'customer' or 'lead'
            details: Interaction details

        Returns:
            Tuple of (success, interaction, error_message)
        """
        try:
            # Prepare interaction data
            # TODO: InteractionStatus enum doesn't exist - temporarily disabled
            # interaction_data = InteractionCreate(
            #     customer_id=entity_id if entity_type == "customer" else None,
            #     lead_id=entity_id if entity_type == "lead" else None,
            #     interaction_type=interaction_type,
            #     direction=InteractionDirection.OUTBOUND.value,
            #     status=InteractionStatus.COMPLETED.value,
            #     interaction_time=datetime.utcnow().isoformat(),
            #     summary=details.get("summary", f"Auto-logged {interaction_type}"),
            #     notes=details.get("notes"),
            #     assigned_to=details.get("assigned_to"),
            #     metadata=details.get("metadata", {}),
            # )
            # return self.create_interaction(interaction_data, "system")
            logger.warning("log_interaction temporarily disabled - InteractionStatus enum needs to be added")
            return (False, None, "InteractionStatus enum not implemented")

        except Exception as e:
            logger.error(f"Error auto-logging interaction: {str(e)}")
            return False, None, str(e)

    def get_interaction_templates(self, interaction_type: str | None = None) -> list[dict]:
        """
        Get interaction templates for quick logging.

        Args:
            interaction_type: Filter by interaction type

        Returns:
            List of templates
        """
        try:
            client = self._get_client()

            query = client.from_("interaction_templates").select("*").eq("is_active", True)

            if interaction_type:
                query = query.eq("interaction_type", interaction_type)

            result = query.order("usage_count", desc=True).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting interaction templates: {str(e)}")
            return []

    def merge_duplicate_interactions(
        self, interaction_ids: list[str], primary_id: str
    ) -> tuple[bool, str | None]:
        """
        Merge duplicate interactions into a single record.

        Args:
            interaction_ids: List of interaction IDs to merge
            primary_id: Primary interaction ID to keep

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if primary_id not in interaction_ids:
                return False, "Primary ID must be in the list of IDs to merge"

            client = self._get_client()

            # Get all interactions
            result = client.from_("interactions").select("*").in_("id", interaction_ids).execute()
            if not result.data:
                return False, "No interactions found"

            interactions = result.data
            primary = next((i for i in interactions if i["id"] == primary_id), None)
            if not primary:
                return False, "Primary interaction not found"

            # Merge notes and metadata
            all_notes = []
            merged_metadata = {}

            for interaction in interactions:
                if interaction["id"] != primary_id:
                    if interaction.get("notes"):
                        all_notes.append(
                            f"[Merged from {interaction['id']}]: {interaction['notes']}"
                        )
                    if interaction.get("metadata"):
                        merged_metadata.update(interaction["metadata"])

            # Update primary interaction
            update_data = {
                "notes": (
                    primary.get("notes", "") + "\n\n" + "\n".join(all_notes)
                    if all_notes
                    else primary.get("notes")
                ),
                "metadata": {**primary.get("metadata", {}), **merged_metadata},
                "updated_at": datetime.utcnow().isoformat(),
            }

            client.from_("interactions").update(update_data).eq("id", primary_id).execute()

            # Delete duplicate interactions
            duplicates = [id for id in interaction_ids if id != primary_id]
            client.from_("interactions").delete().in_("id", duplicates).execute()

            logger.info(f"Merged {len(duplicates)} interactions into {primary_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error merging interactions: {str(e)}")
            return False, str(e)


# Singleton instance
interaction_service = InteractionService()
