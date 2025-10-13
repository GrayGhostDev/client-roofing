"""
iSwitch Roofs CRM - Lead Service Layer
Version: 1.0.0

Service layer for Lead operations using SQLAlchemy ORM.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import asc, desc

from app.database import get_db_session
from app.models.lead_sqlalchemy import Lead, LeadStatusEnum, LeadTemperatureEnum
from app.schemas.lead import LeadCreate, LeadListFilters, LeadUpdate
from app.services.lead_scoring import lead_scoring_engine
from app.utils.cache import cache_result, cache_invalidate


class LeadService:
    """Service class for Lead operations"""

    @staticmethod
    def create_lead(lead_data: LeadCreate) -> Lead:
        """
        Create a new lead with automatic scoring.

        Args:
            lead_data: Lead creation data

        Returns:
            Lead: Created lead object
        """
        with get_db_session() as db:
            # Create Lead object - don't pass status if not provided
            # Let SQLAlchemy handle the default value
            lead_dict = lead_data.model_dump(exclude={"budget_confirmed", "is_decision_maker"})

            # Remove status if it's None - let SQLAlchemy use the column default
            if 'status' not in lead_dict or lead_dict['status'] is None:
                lead_dict.pop('status', None)

            lead = Lead(**lead_dict)

            # Calculate lead score
            score_breakdown = lead_scoring_engine.calculate_score(
                lead,
                interaction_count=0,
                response_time_minutes=None,
                budget_confirmed=lead_data.budget_confirmed,
                is_decision_maker=lead_data.is_decision_maker,
            )

            # Update lead with score and temperature
            lead.lead_score = score_breakdown.total_score
            lead.temperature = score_breakdown.temperature

            # Add to database
            db.add(lead)
            db.commit()
            db.refresh(lead)

            # Convert to dict while still in session
            lead_dict = lead.to_dict()

            # Invalidate lead stats cache after creation
            cache_invalidate("crm:leads:*")

            return lead_dict

    @staticmethod
    def get_lead_by_id(lead_id: str) -> Lead | None:
        """
        Get a lead by ID.

        Args:
            lead_id: UUID of the lead

        Returns:
            Optional[Lead]: Lead object if found
        """
        with get_db_session() as db:
            return db.query(Lead).filter(Lead.id == lead_id, Lead.is_deleted == False).first()

    @staticmethod
    def get_leads_with_filters(
        filters: LeadListFilters, page: int = 1, per_page: int = 50, sort: str = "created_at:desc"
    ) -> tuple[list[Lead], int]:
        """
        Get leads with filtering, pagination, and sorting.

        Args:
            filters: Filter parameters
            page: Page number
            per_page: Items per page
            sort: Sort field and direction

        Returns:
            tuple: (leads, total_count)
        """
        with get_db_session() as db:
            query = db.query(Lead).filter(Lead.is_deleted == False)

            # Apply filters
            if filters.status:
                statuses = filters.status.split(",")
                query = query.filter(Lead.status.in_(statuses))

            if filters.temperature:
                temps = filters.temperature.split(",")
                query = query.filter(Lead.temperature.in_(temps))

            if filters.source:
                sources = filters.source.split(",")
                query = query.filter(Lead.source.in_(sources))

            if filters.assigned_to:
                query = query.filter(Lead.assigned_to == filters.assigned_to)

            if filters.created_after:
                query = query.filter(Lead.created_at >= filters.created_after)

            if filters.min_score is not None:
                query = query.filter(Lead.lead_score >= filters.min_score)

            if filters.max_score is not None:
                query = query.filter(Lead.lead_score <= filters.max_score)

            if filters.zip_code:
                query = query.filter(Lead.zip_code == filters.zip_code)

            if filters.converted is not None:
                query = query.filter(Lead.converted_to_customer == filters.converted)

            # Get total count
            total = query.count()

            # Apply sorting
            if ":" in sort:
                field, direction = sort.split(":")
                if direction.lower() == "desc":
                    query = query.order_by(desc(getattr(Lead, field, Lead.created_at)))
                else:
                    query = query.order_by(asc(getattr(Lead, field, Lead.created_at)))
            else:
                query = query.order_by(desc(Lead.created_at))

            # Apply pagination
            offset = (page - 1) * per_page
            leads = query.offset(offset).limit(per_page).all()

            # Convert to dictionaries while still in session to avoid detached instance errors
            lead_dicts = [lead.to_dict() for lead in leads]

            return lead_dicts, total

    @staticmethod
    def update_lead(lead_id: str, update_data: LeadUpdate) -> Lead | None:
        """
        Update a lead and recalculate score.

        Args:
            lead_id: UUID of the lead
            update_data: Update data

        Returns:
            Optional[Lead]: Updated lead object if found
        """
        with get_db_session() as db:
            lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_deleted == False).first()

            if not lead:
                return None

            # Apply updates
            update_dict = update_data.model_dump(exclude_none=True)
            for field, value in update_dict.items():
                setattr(lead, field, value)

            # Update timestamp
            lead.updated_at = datetime.utcnow()

            # Recalculate score if relevant fields changed
            scoring_fields = [
                "property_value",
                "zip_code",
                "urgency",
                "budget_range_min",
                "budget_range_max",
                "insurance_claim",
            ]
            if any(field in update_dict for field in scoring_fields):
                score_breakdown = lead_scoring_engine.recalculate_lead_score(
                    lead, interaction_count=lead.interaction_count
                )
                lead.lead_score = score_breakdown.total_score
                lead.temperature = score_breakdown.temperature

            db.commit()
            db.refresh(lead)

            # Invalidate lead cache after update
            cache_invalidate("crm:leads:*")

            return lead

    @staticmethod
    def delete_lead(lead_id: str) -> bool:
        """
        Soft delete a lead.

        Args:
            lead_id: UUID of the lead

        Returns:
            bool: True if deleted successfully
        """
        with get_db_session() as db:
            lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_deleted == False).first()

            if not lead:
                return False

            lead.soft_delete()
            db.commit()

            return True

    @staticmethod
    @cache_result(ttl=30, key_prefix="leads")
    def get_hot_leads() -> list[Lead]:
        """
        Get all hot leads (score >= 80).
        Cached for 30s (real-time priority).

        Returns:
            List[Lead]: List of hot leads
        """
        with get_db_session() as db:
            return (
                db.query(Lead)
                .filter(
                    Lead.is_deleted == False,
                    Lead.lead_score >= 80,
                    Lead.temperature == LeadTemperatureEnum.HOT,
                )
                .order_by(desc(Lead.lead_score))
                .all()
            )

    @staticmethod
    def convert_lead_to_customer(lead_id: str, customer_id: str | None = None) -> Lead | None:
        """
        Convert a lead to a customer.

        Args:
            lead_id: UUID of the lead
            customer_id: UUID of the customer (optional)

        Returns:
            Optional[Lead]: Updated lead if found
        """
        with get_db_session() as db:
            lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_deleted == False).first()

            if not lead:
                return None

            lead.converted_to_customer = True
            lead.customer_id = customer_id
            lead.status = LeadStatusEnum.WON
            lead.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(lead)

            return lead

    @staticmethod
    def assign_lead(lead_id: str, team_member_id: str, notes: str | None = None) -> Lead | None:
        """
        Assign a lead to a team member.

        Args:
            lead_id: UUID of the lead
            team_member_id: UUID of the team member
            notes: Optional assignment notes

        Returns:
            Optional[Lead]: Updated lead if found
        """
        with get_db_session() as db:
            lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_deleted == False).first()

            if not lead:
                return None

            lead.assigned_to = team_member_id
            lead.updated_at = datetime.utcnow()

            # Update status to contacted if still new
            if lead.status == LeadStatusEnum.NEW:
                lead.status = LeadStatusEnum.CONTACTED

            # Add notes if provided
            if notes:
                existing_notes = lead.notes or ""
                lead.notes = (
                    f"{existing_notes}\n[Assignment] {notes}"
                    if existing_notes
                    else f"[Assignment] {notes}"
                )

            db.commit()
            db.refresh(lead)

            return lead

    @staticmethod
    @cache_result(ttl=300, key_prefix="leads")
    def get_lead_stats() -> dict[str, Any]:
        """
        Get lead statistics and KPIs.
        Cached for 5min (standard dashboard data).

        Returns:
            Dict: Lead statistics
        """
        with get_db_session() as db:
            # Temperature counts
            hot_count = (
                db.query(Lead)
                .filter(Lead.is_deleted == False, Lead.temperature == LeadTemperatureEnum.HOT)
                .count()
            )

            warm_count = (
                db.query(Lead)
                .filter(Lead.is_deleted == False, Lead.temperature == LeadTemperatureEnum.WARM)
                .count()
            )

            cool_count = (
                db.query(Lead)
                .filter(Lead.is_deleted == False, Lead.temperature == LeadTemperatureEnum.COOL)
                .count()
            )

            cold_count = (
                db.query(Lead)
                .filter(Lead.is_deleted == False, Lead.temperature == LeadTemperatureEnum.COLD)
                .count()
            )

            # Status counts
            new_count = (
                db.query(Lead)
                .filter(Lead.is_deleted == False, Lead.status == LeadStatusEnum.NEW)
                .count()
            )

            qualified_count = (
                db.query(Lead)
                .filter(Lead.is_deleted == False, Lead.status == LeadStatusEnum.QUALIFIED)
                .count()
            )

            # Total and conversion metrics
            total_leads = db.query(Lead).filter(Lead.is_deleted == False).count()
            converted_count = (
                db.query(Lead)
                .filter(Lead.is_deleted == False, Lead.converted_to_customer == True)
                .count()
            )

            conversion_rate = (converted_count / total_leads * 100) if total_leads > 0 else 0

            return {
                "total_leads": total_leads,
                "by_temperature": {
                    "hot": hot_count,
                    "warm": warm_count,
                    "cool": cool_count,
                    "cold": cold_count,
                },
                "by_status": {"new": new_count, "qualified": qualified_count},
                "conversion": {
                    "converted_count": converted_count,
                    "conversion_rate": round(conversion_rate, 2),
                },
            }

    @staticmethod
    def recalculate_lead_score(lead_id: str, **kwargs) -> tuple[Lead, dict[str, Any]] | None:
        """
        Manually recalculate lead score.

        Args:
            lead_id: UUID of the lead
            **kwargs: Additional scoring parameters

        Returns:
            Optional[tuple]: (lead, score_breakdown) if found
        """
        with get_db_session() as db:
            lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_deleted == False).first()

            if not lead:
                return None

            # Get scoring parameters
            interaction_count = kwargs.get("interaction_count", lead.interaction_count)
            response_time_minutes = kwargs.get("response_time_minutes", lead.response_time_minutes)
            budget_confirmed = kwargs.get("budget_confirmed", False)
            is_decision_maker = kwargs.get("is_decision_maker", False)

            # Recalculate score
            score_breakdown = lead_scoring_engine.calculate_score(
                lead,
                interaction_count=interaction_count,
                response_time_minutes=response_time_minutes,
                budget_confirmed=budget_confirmed,
                is_decision_maker=is_decision_maker,
            )

            # Update lead
            lead.lead_score = score_breakdown.total_score
            lead.temperature = score_breakdown.temperature
            lead.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(lead)

            return lead, score_breakdown.model_dump()


# Create service instance
lead_service = LeadService()
