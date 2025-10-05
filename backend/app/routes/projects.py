"""
iSwitch Roofs CRM - Projects API Routes
Version: 1.0.0

Complete project management API with scheduling, resource allocation,
profitability tracking, and document management.
"""

from flask import Blueprint, request, jsonify, g, send_file
import logging
from datetime import datetime
import io
import csv

from app.utils.auth import require_auth, require_role
from app.utils.validation import validate_request, validate_uuid
from app.utils.supabase_client import get_supabase_client
from app.services.project_service import project_service
from app.services.realtime_service import realtime_service
from app.models.project_sqlalchemy import (
    ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema,
    ProjectStatus, ProjectType, ProjectPriority
)

bp = Blueprint('projects', __name__)
logger = logging.getLogger(__name__)


@bp.route('/', methods=['GET'])
@require_auth
def list_projects():
    """
    List all projects with filtering and pagination.

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 100)
        - status: Filter by status (comma-separated)
        - type: Filter by project type
        - customer_id: Filter by customer
        - assigned_to: Filter by assigned user
        - priority: Filter by priority
        - start_date_from: Filter by start date range
        - start_date_to: Filter by start date range
        - min_value: Minimum project value
        - max_value: Maximum project value
        - is_delayed: Filter delayed projects (true/false)
        - sort: Sort field and direction (field:asc/desc)

    Returns:
        JSON response with projects list and pagination
    """
    try:
        supabase = get_supabase_client()

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        offset = (page - 1) * per_page

        # Build query
        query = supabase.from_('projects').select('*')

        # Apply filters
        if status := request.args.get('status'):
            statuses = status.split(',')
            query = query.in_('status', statuses)

        if project_type := request.args.get('type'):
            query = query.eq('project_type', project_type)

        if customer_id := request.args.get('customer_id'):
            query = query.eq('customer_id', customer_id)

        if assigned_to := request.args.get('assigned_to'):
            query = query.eq('assigned_to', assigned_to)

        if priority := request.args.get('priority'):
            query = query.eq('priority', priority)

        # Date range filters
        if start_from := request.args.get('start_date_from'):
            query = query.gte('start_date', start_from)

        if start_to := request.args.get('start_date_to'):
            query = query.lte('start_date', start_to)

        # Value filters
        if min_value := request.args.get('min_value'):
            query = query.gte('estimated_value', float(min_value))

        if max_value := request.args.get('max_value'):
            query = query.lte('estimated_value', float(max_value))

        # Delayed projects filter
        if is_delayed := request.args.get('is_delayed'):
            if is_delayed.lower() == 'true':
                # Projects past end date but not completed
                query = query.lte('end_date', datetime.utcnow().isoformat()).neq('status', ProjectStatus.COMPLETED.value)

        # Sorting
        sort_field = 'created_at'
        sort_dir = 'desc'
        if sort := request.args.get('sort'):
            parts = sort.split(':')
            sort_field = parts[0]
            sort_dir = parts[1] if len(parts) > 1 else 'asc'

        query = query.order(sort_field, desc=(sort_dir == 'desc'))

        # Execute query with pagination
        result = query.range(offset, offset + per_page - 1).execute()
        projects = result.data

        # Get total count
        count_result = supabase.from_('projects').select('*', count='exact').execute()
        total = count_result.count if hasattr(count_result, 'count') else len(projects)

        # Calculate summary statistics
        stats = {
            'total_projects': total,
            'active_projects': len([p for p in projects if p['status'] == ProjectStatus.IN_PROGRESS.value]),
            'completed_projects': len([p for p in projects if p['status'] == ProjectStatus.COMPLETED.value]),
            'total_value': sum(p.get('estimated_value', 0) for p in projects),
            'average_value': sum(p.get('estimated_value', 0) for p in projects) / len(projects) if projects else 0
        }

        response = {
            'data': projects,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page,
                'has_next': page * per_page < total,
                'has_prev': page > 1
            },
            'stats': stats
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return jsonify({'error': 'Failed to list projects'}), 500


@bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_project(project_id: str):
    """
    Get project by ID with full details.

    Path Parameters:
        - project_id: Project UUID

    Query Parameters:
        - include: Comma-separated list of related data to include
                  (timeline, profitability, resources, documents, history)

    Returns:
        JSON response with project details
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        supabase = get_supabase_client()

        # Get project
        result = supabase.from_('projects').select('*').eq('id', project_id).execute()

        if not result.data:
            return jsonify({'error': 'Project not found'}), 404

        project = result.data[0]

        # Get customer details
        customer_result = supabase.from_('customers').select('first_name, last_name, email, phone').eq('id', project['customer_id']).execute()
        if customer_result.data:
            project['customer'] = customer_result.data[0]

        # Include additional data based on query params
        includes = request.args.get('include', '').split(',')

        if 'timeline' in includes:
            project['timeline'] = project_service.get_project_timeline(project_id)

        if 'profitability' in includes:
            project['profitability'] = project_service.calculate_project_profitability(project_id)

        if 'resources' in includes:
            project['resources'] = project_service.get_project_resources(project_id)

        if 'documents' in includes:
            project['documents'] = project_service.get_project_documents(project_id)

        if 'history' in includes:
            # Get project history/audit log
            history_result = supabase.from_('project_history').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(50).execute()
            project['history'] = history_result.data if history_result.data else []

        return jsonify(project), 200

    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        return jsonify({'error': 'Failed to get project'}), 500


@bp.route('/', methods=['POST'])
@require_auth
@validate_request(ProjectCreateSchema)
def create_project():
    """
    Create a new project.

    Request Body:
        - ProjectCreate model fields

    Returns:
        JSON response with created project
    """
    try:
        project_data = ProjectCreateSchema(**request.validated_data)
        user_id = g.user_id

        success, project, error = project_service.create_project(project_data, user_id)

        if success:
            # Broadcast real-time event
            realtime_service.trigger_event(
                channel='projects',
                event='project-created',
                data={'project': project}
            )

            return jsonify(project), 201
        else:
            return jsonify({'error': error or 'Failed to create project'}), 400

    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({'error': 'Failed to create project'}), 500


@bp.route('/<project_id>', methods=['PUT', 'PATCH'])
@require_auth
def update_project(project_id: str):
    """
    Update an existing project.

    Path Parameters:
        - project_id: Project UUID

    Request Body:
        - ProjectUpdate model fields (partial update supported)

    Returns:
        JSON response with updated project
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No update data provided'}), 400

        update_data = ProjectUpdateSchema(**data)
        user_id = g.user_id

        success, project, error = project_service.update_project(project_id, update_data, user_id)

        if success:
            # Broadcast real-time event
            realtime_service.trigger_event(
                channel='projects',
                event='project-updated',
                data={'project': project}
            )

            return jsonify(project), 200
        else:
            if error == "Project not found":
                return jsonify({'error': error}), 404
            return jsonify({'error': error or 'Failed to update project'}), 400

    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        return jsonify({'error': 'Failed to update project'}), 500


@bp.route('/<project_id>', methods=['DELETE'])
@require_role('admin')
def delete_project(project_id: str):
    """
    Delete a project (soft delete).

    Path Parameters:
        - project_id: Project UUID

    Returns:
        JSON response with success message
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        supabase = get_supabase_client()

        # Check if project exists
        result = supabase.from_('projects').select('id').eq('id', project_id).execute()

        if not result.data:
            return jsonify({'error': 'Project not found'}), 404

        # Soft delete by updating status
        update_result = supabase.from_('projects').update({
            'status': ProjectStatus.CANCELLED.value,
            'deleted_at': datetime.utcnow().isoformat(),
            'deleted_by': g.user_id
        }).eq('id', project_id).execute()

        if update_result.data:
            # Broadcast real-time event
            realtime_service.trigger_event(
                channel='projects',
                event='project-deleted',
                data={'project_id': project_id}
            )

            return jsonify({'message': 'Project deleted successfully'}), 200

        return jsonify({'error': 'Failed to delete project'}), 500

    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        return jsonify({'error': 'Failed to delete project'}), 500


@bp.route('/<project_id>/timeline', methods=['GET'])
@require_auth
def get_project_timeline(project_id: str):
    """
    Get project timeline and milestones.

    Path Parameters:
        - project_id: Project UUID

    Returns:
        JSON response with timeline data
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        timeline = project_service.get_project_timeline(project_id)

        if timeline:
            return jsonify(timeline), 200
        else:
            return jsonify({'error': 'Project not found'}), 404

    except Exception as e:
        logger.error(f"Error getting project timeline: {str(e)}")
        return jsonify({'error': 'Failed to get timeline'}), 500


@bp.route('/<project_id>/profitability', methods=['GET'])
@require_auth
def get_project_profitability(project_id: str):
    """
    Get project profitability analysis.

    Path Parameters:
        - project_id: Project UUID

    Returns:
        JSON response with profitability metrics
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        profitability = project_service.calculate_project_profitability(project_id)

        if profitability:
            return jsonify(profitability), 200
        else:
            return jsonify({'error': 'Project not found'}), 404

    except Exception as e:
        logger.error(f"Error calculating profitability: {str(e)}")
        return jsonify({'error': 'Failed to calculate profitability'}), 500


@bp.route('/<project_id>/resources', methods=['GET'])
@require_auth
def get_project_resources(project_id: str):
    """
    Get project resource allocation.

    Path Parameters:
        - project_id: Project UUID

    Returns:
        JSON response with resource data
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        resources = project_service.get_project_resources(project_id)

        if resources:
            return jsonify(resources), 200
        else:
            return jsonify({'error': 'Project not found'}), 404

    except Exception as e:
        logger.error(f"Error getting project resources: {str(e)}")
        return jsonify({'error': 'Failed to get resources'}), 500


@bp.route('/<project_id>/schedule', methods=['POST'])
@require_auth
def schedule_project(project_id: str):
    """
    Schedule a project.

    Path Parameters:
        - project_id: Project UUID

    Request Body:
        - start_date: ISO format datetime
        - crew_id: Optional crew assignment

    Returns:
        JSON response with schedule data
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        data = request.get_json()
        if not data or 'start_date' not in data:
            return jsonify({'error': 'Start date is required'}), 400

        start_date = datetime.fromisoformat(data['start_date'])
        crew_id = data.get('crew_id')

        success, schedule, error = project_service.schedule_project(project_id, start_date, crew_id)

        if success:
            return jsonify(schedule), 200
        else:
            return jsonify({'error': error or 'Failed to schedule project'}), 400

    except Exception as e:
        logger.error(f"Error scheduling project: {str(e)}")
        return jsonify({'error': 'Failed to schedule project'}), 500


@bp.route('/<project_id>/documents', methods=['GET'])
@require_auth
def get_project_documents(project_id: str):
    """
    Get all documents for a project.

    Path Parameters:
        - project_id: Project UUID

    Returns:
        JSON response with documents list
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        documents = project_service.get_project_documents(project_id)
        return jsonify({'data': documents}), 200

    except Exception as e:
        logger.error(f"Error getting project documents: {str(e)}")
        return jsonify({'error': 'Failed to get documents'}), 500


@bp.route('/<project_id>/documents', methods=['POST'])
@require_auth
def add_project_document(project_id: str):
    """
    Add a document to a project.

    Path Parameters:
        - project_id: Project UUID

    Request Body:
        - name: Document name
        - type: Document type
        - url: Document URL or path
        - description: Optional description

    Returns:
        JSON response with created document
    """
    try:
        if not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        data = request.get_json()
        if not data or 'name' not in data or 'url' not in data:
            return jsonify({'error': 'Document name and URL are required'}), 400

        document_data = {
            'name': data['name'],
            'type': data.get('type', 'document'),
            'url': data['url'],
            'description': data.get('description'),
            'uploaded_by': g.user_id
        }

        success, document, error = project_service.add_project_document(project_id, document_data)

        if success:
            return jsonify(document), 201
        else:
            return jsonify({'error': error or 'Failed to add document'}), 400

    except Exception as e:
        logger.error(f"Error adding project document: {str(e)}")
        return jsonify({'error': 'Failed to add document'}), 500


@bp.route('/stats/overview', methods=['GET'])
@require_auth
def get_projects_overview():
    """
    Get projects overview statistics.

    Query Parameters:
        - period: Time period (week, month, quarter, year)
        - assigned_to: Filter by assigned user

    Returns:
        JSON response with overview statistics
    """
    try:
        supabase = get_supabase_client()

        # Build query
        query = supabase.from_('projects').select('*')

        # Apply filters
        if assigned_to := request.args.get('assigned_to'):
            query = query.eq('assigned_to', assigned_to)

        # Get time period filter
        period = request.args.get('period', 'month')
        if period == 'week':
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date -= timedelta(days=start_date.weekday())
        elif period == 'month':
            start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'quarter':
            month = datetime.utcnow().month
            quarter_start_month = 3 * ((month - 1) // 3) + 1
            start_date = datetime.utcnow().replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # year
            start_date = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        query = query.gte('created_at', start_date.isoformat())

        result = query.execute()
        projects = result.data if result.data else []

        # Calculate statistics
        total_projects = len(projects)
        completed_projects = len([p for p in projects if p['status'] == ProjectStatus.COMPLETED.value])
        active_projects = len([p for p in projects if p['status'] == ProjectStatus.IN_PROGRESS.value])
        scheduled_projects = len([p for p in projects if p['status'] == ProjectStatus.SCHEDULED.value])

        total_value = sum(p.get('estimated_value', 0) for p in projects)
        actual_value = sum(p.get('actual_value', 0) for p in projects if p.get('actual_value'))

        # Calculate average completion time
        completed = [p for p in projects if p['status'] == ProjectStatus.COMPLETED.value and p.get('start_date') and p.get('end_date')]
        if completed:
            completion_times = [(datetime.fromisoformat(p['end_date']) - datetime.fromisoformat(p['start_date'])).days for p in completed]
            avg_completion_time = sum(completion_times) / len(completion_times)
        else:
            avg_completion_time = 0

        # Calculate profitability
        total_profit = 0
        for project in projects:
            if project.get('actual_value') or project.get('estimated_value'):
                value = project.get('actual_value') or project.get('estimated_value', 0)
                costs = project.get('materials_cost', 0) + project.get('labor_cost', 0) + project.get('subcontractor_cost', 0) + project.get('other_costs', 0)
                total_profit += (value - costs)

        overview = {
            'period': period,
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'active_projects': active_projects,
            'scheduled_projects': scheduled_projects,
            'completion_rate': (completed_projects / total_projects * 100) if total_projects > 0 else 0,
            'total_estimated_value': total_value,
            'total_actual_value': actual_value,
            'total_profit': total_profit,
            'average_completion_time_days': round(avg_completion_time, 1),
            'projects_by_type': {},
            'projects_by_priority': {},
            'delayed_projects': 0
        }

        # Count by type
        for project_type in ProjectType:
            overview['projects_by_type'][project_type.value] = len([p for p in projects if p.get('project_type') == project_type.value])

        # Count by priority
        for priority in ProjectPriority:
            overview['projects_by_priority'][priority.value] = len([p for p in projects if p.get('priority') == priority.value])

        # Count delayed projects
        now = datetime.utcnow()
        overview['delayed_projects'] = len([p for p in projects if p.get('end_date') and datetime.fromisoformat(p['end_date']) < now and p['status'] != ProjectStatus.COMPLETED.value])

        return jsonify(overview), 200

    except Exception as e:
        logger.error(f"Error getting projects overview: {str(e)}")
        return jsonify({'error': 'Failed to get overview'}), 500


@bp.route('/export', methods=['GET'])
@require_auth
def export_projects():
    """
    Export projects to CSV.

    Query Parameters:
        - status: Filter by status
        - start_date_from: Filter by date range
        - start_date_to: Filter by date range

    Returns:
        CSV file download
    """
    try:
        supabase = get_supabase_client()

        # Build query
        query = supabase.from_('projects').select('*')

        # Apply filters
        if status := request.args.get('status'):
            query = query.eq('status', status)

        if start_from := request.args.get('start_date_from'):
            query = query.gte('start_date', start_from)

        if start_to := request.args.get('start_date_to'):
            query = query.lte('start_date', start_to)

        result = query.execute()
        projects = result.data if result.data else []

        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'name', 'customer_id', 'project_type', 'status', 'priority',
            'estimated_value', 'actual_value', 'materials_cost', 'labor_cost',
            'profit_margin', 'start_date', 'end_date', 'assigned_to', 'created_at'
        ])
        writer.writeheader()
        writer.writerows(projects)

        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'projects_export_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        logger.error(f"Error exporting projects: {str(e)}")
        return jsonify({'error': 'Failed to export projects'}), 500