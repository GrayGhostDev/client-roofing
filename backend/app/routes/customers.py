"""
Customer API Routes
Version: 1.0.0

RESTful API endpoints for customer management with full CRUD operations.
"""

import io
import logging
from datetime import datetime
from uuid import UUID

from flask import Blueprint, Response, g, jsonify, request

from app.config import get_supabase_client
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
)
from app.services.customer_service import customer_service
from app.services.notification import notification_service
from app.utils.auth import require_auth
from app.utils.validation import validate_request
from app.utils.pusher_client import get_pusher_service

bp = Blueprint("customers", __name__, url_prefix="/api/customers")
logger = logging.getLogger(__name__)

# Initialize clients
supabase_client = None
pusher_service = get_pusher_service()


def get_supabase():
    """Get or initialize Supabase client."""
    global supabase_client
    if not supabase_client:
        supabase_client = get_supabase_client()
    return supabase_client


@bp.route("/", methods=["GET"])
@require_auth
def list_customers():
    """
    List all customers with filtering and pagination.

    Query Parameters:
        - page: Page number (default: 1)
        - limit: Items per page (default: 50, max: 100)
        - sort: Sort field:direction (e.g., 'created_at:desc')
        - status: Filter by status (comma-separated)
        - segment: Filter by segment (comma-separated)
        - assigned_to: Filter by assigned team member
        - min_lifetime_value: Minimum lifetime value
        - zip_code: Filter by ZIP code
        - city: Filter by city
        - is_referral_partner: Filter referral partners
    """
    try:
        from app.utils.database import get_db_session
        from app.utils.pagination import paginate_query, create_pagination_response
        from sqlalchemy import and_
        from app.models.customer_sqlalchemy import Customer

        # Pagination parameters
        page = int(request.args.get("page", 1))
        limit = min(int(request.args.get("limit", 50)), 100)

        # Build query using SQLAlchemy
        db = get_db_session()
        query = db.query(Customer).filter(Customer.is_deleted == False)

        # Apply filters
        filters = []

        if status := request.args.get("status"):
            statuses = status.split(",")
            filters.append(Customer.status.in_(statuses))

        if segment := request.args.get("segment"):
            segments = segment.split(",")
            filters.append(Customer.segment.in_(segments))

        if assigned_to := request.args.get("assigned_to"):
            filters.append(Customer.assigned_to == assigned_to)

        if min_ltv := request.args.get("min_lifetime_value"):
            filters.append(Customer.lifetime_value >= int(min_ltv))

        if zip_code := request.args.get("zip_code"):
            filters.append(Customer.zip_code == zip_code)

        if city := request.args.get("city"):
            filters.append(Customer.city == city)

        if is_referral := request.args.get("is_referral_partner"):
            filters.append(Customer.is_referral_partner == (is_referral.lower() == "true"))

        if filters:
            query = query.filter(and_(*filters))

        # Sorting
        sort_field = "created_at"
        sort_dir = "desc"
        if sort := request.args.get("sort"):
            parts = sort.split(":")
            sort_field = parts[0]
            sort_dir = parts[1] if len(parts) > 1 else "asc"

        # Apply sorting
        if hasattr(Customer, sort_field):
            order_column = getattr(Customer, sort_field)
            if sort_dir == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            # Default sort
            query = query.order_by(Customer.created_at.desc())

        # Get paginated results
        customers, total = paginate_query(query, page=page, per_page=limit)

        # Convert SQLAlchemy models to dicts
        customers_data = []
        for customer in customers:
            customer_dict = {
                "id": str(customer.id),
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone": customer.phone,
                "status": customer.status.value if customer.status else None,
                "segment": customer.segment.value if customer.segment else None,
                "lifetime_value": customer.lifetime_value,
                "project_count": customer.project_count,
                "street_address": customer.street_address,
                "city": customer.city,
                "state": customer.state,
                "zip_code": customer.zip_code,
                "assigned_to": customer.assigned_to,
                "is_referral_partner": customer.is_referral_partner,
                "referral_count": customer.referral_count,
                "nps_score": customer.nps_score,
                "customer_since": customer.customer_since.isoformat() if customer.customer_since else None,
                "last_interaction": customer.last_interaction.isoformat() if customer.last_interaction else None,
                "created_at": customer.created_at.isoformat() if customer.created_at else None,
                "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
            }
            customers_data.append(customer_dict)

        # Create pagination response
        response = create_pagination_response(
            items=customers_data,
            total=total,
            page=page,
            per_page=limit
        )

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to list customers"}), 500


@bp.route("/<customer_id>", methods=["GET"])
@require_auth
def get_customer(customer_id: str):
    """
    Get customer by ID with optional history.

    Path Parameters:
        - customer_id: Customer UUID

    Query Parameters:
        - include_history: Include interaction history (default: false)
        - include_projects: Include project list (default: false)
    """
    try:
        supabase = get_supabase()

        # Validate UUID
        try:
            UUID(customer_id)
        except ValueError:
            return jsonify({"error": "Invalid customer ID format"}), 400

        # Get customer
        result = supabase.from_("customers").select("*").eq("id", customer_id).single().execute()

        if not result.data:
            return jsonify({"error": "Customer not found"}), 404

        customer = result.data
        response = {"data": customer}

        # Include interaction history if requested
        if request.args.get("include_history") == "true":
            interactions = (
                supabase.from_("interactions")
                .select("*")
                .eq("customer_id", customer_id)
                .order("created_at", desc=True)
                .limit(20)
                .execute()
            )
            response["interaction_history"] = interactions.data

        # Include projects if requested
        if request.args.get("include_projects") == "true":
            projects = (
                supabase.from_("projects")
                .select("*")
                .eq("customer_id", customer_id)
                .order("created_at", desc=True)
                .execute()
            )
            response["projects"] = projects.data

        # Generate insights
        interactions = response.get("interaction_history", [])
        projects = response.get("projects", [])
        insights = customer_service.get_customer_insights(
            customer, interactions, projects  # Already a dict from database
        )
        response["insights"] = insights

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {str(e)}")
        return jsonify({"error": "Failed to get customer"}), 500


@bp.route("/", methods=["POST"])
@require_auth
@validate_request(CustomerCreate)
def create_customer():
    """
    Create a new customer.

    Request Body:
        - CustomerCreate schema
    """
    try:
        supabase = get_supabase()
        data = request.get_json()

        # Check for duplicate email
        if email := data.get("email"):
            existing = supabase.from_("customers").select("id").eq("email", email).execute()
            if existing.data:
                return jsonify({"error": "Customer with this email already exists"}), 409

        # Set audit fields
        data["created_by"] = g.get("user_id")
        data["created_by_email"] = g.get("user_email")
        data["updated_by"] = g.get("user_id")
        data["updated_by_email"] = g.get("user_email")

        # Set timestamps
        now = datetime.utcnow().isoformat()
        data["created_at"] = now
        data["updated_at"] = now

        # If converting from lead, set conversion date
        if data.get("converted_from_lead_id"):
            data["conversion_date"] = now
            data["customer_since"] = now

        # Create customer
        result = supabase.from_("customers").insert(data).execute()

        if not result.data:
            return jsonify({"error": "Failed to create customer"}), 500

        customer = result.data[0]

        # Send notification
        notification_service.send_notification(
            type="customer_created",
            data={
                "customer_id": customer["id"],
                "name": f"{customer['first_name']} {customer['last_name']}",
            },
        )

        # Broadcast customer creation event using PusherService
        try:
            # Note: PusherService.broadcast_customer_created expects specific format
            pusher_service.trigger(
                pusher_service.CHANNEL_CUSTOMERS,
                pusher_service.EVENT_CUSTOMER_CREATED,
                customer
            )
            logger.debug(f"Broadcasted customer:created event for customer {customer['id']}")
        except Exception as pusher_error:
            logger.warning(f"Failed to broadcast customer creation event: {str(pusher_error)}")

        logger.info(f"Customer created: {customer['id']}")
        return jsonify({"data": customer}), 201

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        return jsonify({"error": "Failed to create customer"}), 500


@bp.route("/<customer_id>", methods=["PUT"])
@require_auth
@validate_request(CustomerUpdate)
def update_customer(customer_id: str):
    """
    Update a customer.

    Path Parameters:
        - customer_id: Customer UUID
    """
    try:
        supabase = get_supabase()
        data = request.get_json()

        # Validate UUID
        try:
            UUID(customer_id)
        except ValueError:
            return jsonify({"error": "Invalid customer ID format"}), 400

        # Set audit fields
        data["updated_by"] = g.get("user_id")
        data["updated_by_email"] = g.get("user_email")
        data["updated_at"] = datetime.utcnow().isoformat()

        # Update customer
        result = supabase.from_("customers").update(data).eq("id", customer_id).execute()

        if not result.data:
            return jsonify({"error": "Customer not found"}), 404

        customer = result.data[0]

        # Determine new segment if LTV changed
        if "lifetime_value" in data or "project_count" in data:
            new_segment = customer_service.determine_segment_from_dict(customer)
            if new_segment != customer.get("segment"):
                # Update segment
                segment_update = (
                    supabase.from_("customers")
                    .update({"segment": new_segment})
                    .eq("id", customer_id)
                    .execute()
                )
                customer["segment"] = new_segment

        # Broadcast customer update event using PusherService
        try:
            pusher_service.trigger(
                pusher_service.CHANNEL_CUSTOMERS,
                pusher_service.EVENT_CUSTOMER_UPDATED,
                customer
            )
            logger.debug(f"Broadcasted customer:updated event for customer {customer_id}")
        except Exception as pusher_error:
            logger.warning(f"Failed to broadcast customer update event: {str(pusher_error)}")

        logger.info(f"Customer updated: {customer_id}")
        return jsonify({"data": customer}), 200

    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        return jsonify({"error": "Failed to update customer"}), 500


@bp.route("/<customer_id>", methods=["DELETE"])
@require_auth
def delete_customer(customer_id: str):
    """
    Soft delete a customer.

    Path Parameters:
        - customer_id: Customer UUID
    """
    try:
        supabase = get_supabase()

        # Validate UUID
        try:
            UUID(customer_id)
        except ValueError:
            return jsonify({"error": "Invalid customer ID format"}), 400

        # Soft delete (mark as deleted)
        data = {
            "deleted": True,
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": g.get("user_id"),
            "deleted_by_email": g.get("user_email"),
        }

        result = supabase.from_("customers").update(data).eq("id", customer_id).execute()

        if not result.data:
            return jsonify({"error": "Customer not found"}), 404

        logger.info(f"Customer soft deleted: {customer_id}")
        return jsonify({"message": f"Customer {customer_id} deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {str(e)}")
        return jsonify({"error": "Failed to delete customer"}), 500


@bp.route("/<customer_id>/projects", methods=["GET"])
@require_auth
def get_customer_projects(customer_id: str):
    """
    Get all projects for a customer.

    Path Parameters:
        - customer_id: Customer UUID
    """
    try:
        supabase = get_supabase()

        # Validate UUID
        try:
            UUID(customer_id)
        except ValueError:
            return jsonify({"error": "Invalid customer ID format"}), 400

        # Get projects
        result = (
            supabase.from_("projects")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .execute()
        )

        projects = result.data
        count = len(projects)

        # Calculate total value
        total_value = sum(p.get("total_amount", 0) for p in projects)

        response = {"data": projects, "count": count, "total_value": total_value}

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error getting projects for customer {customer_id}: {str(e)}")
        return jsonify({"error": "Failed to get customer projects"}), 500


@bp.route("/<customer_id>/interactions", methods=["GET"])
@require_auth
def get_customer_interactions(customer_id: str):
    """
    Get interaction history for a customer.

    Path Parameters:
        - customer_id: Customer UUID

    Query Parameters:
        - limit: Number of interactions to return (default: 50)
        - type: Filter by interaction type
    """
    try:
        supabase = get_supabase()

        # Validate UUID
        try:
            UUID(customer_id)
        except ValueError:
            return jsonify({"error": "Invalid customer ID format"}), 400

        # Build query
        query = supabase.from_("interactions").select("*").eq("customer_id", customer_id)

        # Apply filters
        if interaction_type := request.args.get("type"):
            query = query.eq("type", interaction_type)

        limit = int(request.args.get("limit", 50))
        query = query.order("created_at", desc=True).limit(limit)

        # Execute query
        result = query.execute()
        interactions = result.data

        return jsonify({"data": interactions, "count": len(interactions)}), 200

    except Exception as e:
        logger.error(f"Error getting interactions for customer {customer_id}: {str(e)}")
        return jsonify({"error": "Failed to get customer interactions"}), 500


@bp.route("/<customer_id>/interactions", methods=["POST"])
@require_auth
def create_customer_interaction(customer_id: str):
    """
    Create a new interaction for a customer.

    Path Parameters:
        - customer_id: Customer UUID

    Request Body:
        - type: Interaction type (email, phone_call, meeting, etc.)
        - notes: Interaction notes
        - outcome: Interaction outcome
    """
    try:
        supabase = get_supabase()
        pusher = get_pusher()
        data = request.get_json()

        # Validate UUID
        try:
            UUID(customer_id)
        except ValueError:
            return jsonify({"error": "Invalid customer ID format"}), 400

        # Prepare interaction data
        interaction = {
            "customer_id": customer_id,
            "type": data.get("type", "note"),
            "notes": data.get("notes"),
            "outcome": data.get("outcome"),
            "created_by": g.get("user_id"),
            "created_by_email": g.get("user_email"),
            "created_at": datetime.utcnow().isoformat(),
        }

        # Create interaction
        result = supabase.from_("interactions").insert(interaction).execute()

        if not result.data:
            return jsonify({"error": "Failed to create interaction"}), 500

        created_interaction = result.data[0]

        # Update customer's last interaction date and count
        customer_update = {
            "last_interaction": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Get current interaction count
        customer = (
            supabase.from_("customers")
            .select("interaction_count")
            .eq("id", customer_id)
            .single()
            .execute()
        )
        if customer.data:
            customer_update["interaction_count"] = customer.data.get("interaction_count", 0) + 1

        supabase.from_("customers").update(customer_update).eq("id", customer_id).execute()

        # Real-time update
        pusher.trigger("interactions", "interaction-created", created_interaction)

        logger.info(f"Interaction created for customer {customer_id}")
        return jsonify({"data": created_interaction}), 201

    except Exception as e:
        logger.error(f"Error creating interaction for customer {customer_id}: {str(e)}")
        return jsonify({"error": "Failed to create interaction"}), 500


@bp.route("/<customer_id>/calculate-ltv", methods=["POST"])
@require_auth
def calculate_lifetime_value(customer_id: str):
    """
    Calculate and update customer lifetime value.

    Path Parameters:
        - customer_id: Customer UUID
    """
    try:
        supabase = get_supabase()

        # Validate UUID
        try:
            UUID(customer_id)
        except ValueError:
            return jsonify({"error": "Invalid customer ID format"}), 400

        # Get all customer projects
        projects_result = (
            supabase.from_("projects")
            .select("total_amount, status")
            .eq("customer_id", customer_id)
            .execute()
        )

        projects = projects_result.data

        # Calculate lifetime value
        ltv, project_count = customer_service.calculate_lifetime_value(projects)
        avg_value = customer_service.calculate_average_project_value(ltv, project_count)

        # Update customer
        update_data = {
            "lifetime_value": ltv,
            "project_count": project_count,
            "avg_project_value": avg_value,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = supabase.from_("customers").update(update_data).eq("id", customer_id).execute()

        if not result.data:
            return jsonify({"error": "Customer not found"}), 404

        response = {
            "customer_id": customer_id,
            "lifetime_value": ltv,
            "projects_count": project_count,
            "average_project_value": avg_value,
        }

        logger.info(f"Lifetime value calculated for customer {customer_id}: ${ltv}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error calculating LTV for customer {customer_id}: {str(e)}")
        return jsonify({"error": "Failed to calculate lifetime value"}), 500


@bp.route("/stats", methods=["GET"])
@require_auth
def get_customer_stats():
    """Get aggregate customer statistics."""
    try:
        supabase = get_supabase()

        # Total customers
        total_result = supabase.from_("customers").select("*", count="exact").execute()
        total_customers = total_result.count if hasattr(total_result, "count") else 0

        # Get all customers for aggregations
        customers_result = supabase.from_("customers").select("*").execute()
        customers = customers_result.data

        # Calculate statistics
        total_ltv = sum(c.get("lifetime_value", 0) for c in customers)
        avg_ltv = total_ltv // total_customers if total_customers > 0 else 0

        # Status breakdown
        by_status = {}
        for customer in customers:
            status = customer.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        # Segment breakdown
        by_segment = {}
        for customer in customers:
            segment = customer.get("segment", "unknown")
            by_segment[segment] = by_segment.get(segment, 0) + 1

        # Location breakdown (by city)
        by_location = {}
        for customer in customers:
            city = customer.get("city", "Unknown")
            by_location[city] = by_location.get(city, 0) + 1

        # Source breakdown
        by_source = {}
        for customer in customers:
            source = customer.get("original_source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1

        # NPS breakdown
        promoters = sum(1 for c in customers if c.get("nps_score", 0) >= 9)
        passives = sum(1 for c in customers if 7 <= c.get("nps_score", 0) < 9)
        detractors = sum(1 for c in customers if c.get("nps_score", 0) < 7)

        response = {
            "total_customers": total_customers,
            "total_revenue": total_ltv,
            "avg_lifetime_value": avg_ltv,
            "by_status": by_status,
            "by_segment": by_segment,
            "by_location": by_location,
            "by_source": by_source,
            "nps_breakdown": {
                "promoters": promoters,
                "passives": passives,
                "detractors": detractors,
                "nps_score": (
                    (promoters - detractors) / total_customers * 100 if total_customers > 0 else 0
                ),
            },
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error getting customer stats: {str(e)}")
        return jsonify({"error": "Failed to get customer statistics"}), 500


@bp.route("/bulk-update", methods=["POST"])
@require_auth
def bulk_update_customers():
    """
    Bulk update multiple customers.

    Request Body:
        - customer_ids: List of customer UUIDs
        - updates: Dictionary of fields to update
    """
    try:
        supabase = get_supabase()
        data = request.get_json()

        customer_ids = data.get("customer_ids", [])
        updates = data.get("updates", {})

        if not customer_ids or not updates:
            return jsonify({"error": "customer_ids and updates are required"}), 400

        # Add audit fields
        updates["updated_by"] = g.get("user_id")
        updates["updated_by_email"] = g.get("user_email")
        updates["updated_at"] = datetime.utcnow().isoformat()

        # Perform bulk update
        result = supabase.from_("customers").update(updates).in_("id", customer_ids).execute()

        updated = len(result.data) if result.data else 0

        response = {
            "message": f"Updated {updated} customers",
            "updated": updated,
            "requested": len(customer_ids),
        }

        logger.info(f"Bulk updated {updated} customers")
        return jsonify(response), 207  # Multi-status for partial success

    except Exception as e:
        logger.error(f"Error bulk updating customers: {str(e)}")
        return jsonify({"error": "Failed to bulk update customers"}), 500


@bp.route("/export", methods=["GET"])
@require_auth
def export_customers():
    """
    Export customers to CSV format.

    Query Parameters:
        - format: Export format (csv only for now)
        - fields: Comma-separated list of fields to include
        - filters: Same as list endpoint filters
    """
    try:
        supabase = get_supabase()

        # Get customers with same filters as list endpoint
        query = supabase.from_("customers").select("*")

        # Apply filters (same as list_customers)
        if status := request.args.get("status"):
            statuses = status.split(",")
            query = query.in_("status", statuses)

        if segment := request.args.get("segment"):
            segments = segment.split(",")
            query = query.in_("segment", segments)

        result = query.execute()
        customers = result.data

        # Get requested fields
        fields = None
        if field_list := request.args.get("fields"):
            fields = field_list.split(",")

        # Generate CSV (pass dict objects directly)
        csv_data = customer_service.export_customers_csv(customers, fields)

        # Create response
        output = io.StringIO()
        output.write(csv_data)
        output.seek(0)

        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = (
            f'attachment; filename=customers_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )

        logger.info(f"Exported {len(customers)} customers to CSV")
        return response

    except Exception as e:
        logger.error(f"Error exporting customers: {str(e)}")
        return jsonify({"error": "Failed to export customers"}), 500
