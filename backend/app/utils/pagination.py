"""
iSwitch Roofs CRM - Pagination Utility
Version: 1.0.0
Date: 2025-10-09

PURPOSE:
Optimized pagination helpers for efficient data retrieval.
Supports both offset-based and cursor-based pagination.

USAGE:
    from app.utils.pagination import paginate_query, create_pagination_response

    # Offset-based pagination (simple, but slower for large offsets)
    results, total = paginate_query(query, page=1, per_page=50)
    response = create_pagination_response(results, total, page, per_page)

    # Cursor-based pagination (efficient for large datasets)
    results = paginate_cursor(query, cursor=last_id, limit=50)
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Query


def paginate_query(
    query: Query,
    page: int = 1,
    per_page: int = 50,
    max_per_page: int = 100
) -> Tuple[List[Any], int]:
    """
    Paginate a SQLAlchemy query with offset-based pagination.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page (default: 50)
        max_per_page: Maximum items per page (default: 100)

    Returns:
        tuple: (results, total_count)

    Example:
        query = db.query(Lead).filter(Lead.status == 'new')
        results, total = paginate_query(query, page=2, per_page=25)
    """
    # Validate and limit per_page
    page = max(1, page)  # Minimum page 1
    per_page = min(max(1, per_page), max_per_page)  # Between 1 and max_per_page

    # Get total count (before pagination)
    total = query.count()

    # Calculate offset
    offset = (page - 1) * per_page

    # Apply pagination
    results = query.offset(offset).limit(per_page).all()

    return results, total


def create_pagination_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    endpoint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standardized pagination response metadata.

    Args:
        items: List of result items
        total: Total count of items
        page: Current page number
        per_page: Items per page
        endpoint: API endpoint path (optional, for building next/prev links)

    Returns:
        dict: Paginated response with metadata

    Example:
        response = create_pagination_response(
            items=leads,
            total=250,
            page=2,
            per_page=50,
            endpoint="/api/leads"
        )

        # Returns:
        {
            "data": [...items...],
            "pagination": {
                "page": 2,
                "per_page": 50,
                "total_items": 250,
                "total_pages": 5,
                "has_prev": True,
                "has_next": True,
                "prev_page": 1,
                "next_page": 3
            }
        }
    """
    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None

    # Build response
    response = {
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": prev_page,
            "next_page": next_page,
        }
    }

    # Add navigation URLs if endpoint provided
    if endpoint:
        if has_prev:
            response["pagination"]["prev_url"] = f"{endpoint}?page={prev_page}&per_page={per_page}"
        if has_next:
            response["pagination"]["next_url"] = f"{endpoint}?page={next_page}&per_page={per_page}"

    return response


def paginate_cursor(
    query: Query,
    cursor_field: str,
    cursor_value: Optional[Any] = None,
    limit: int = 50,
    order: str = "desc"
) -> List[Any]:
    """
    Cursor-based pagination for efficient large dataset traversal.

    Cursor pagination is more efficient than offset pagination for large datasets
    because it doesn't need to skip rows.

    Args:
        query: SQLAlchemy query object
        cursor_field: Field name to use for cursor (e.g., "created_at", "id")
        cursor_value: Current cursor value (None for first page)
        limit: Items to return
        order: Sort order ("desc" or "asc")

    Returns:
        list: Query results

    Example:
        # First page
        leads = paginate_cursor(
            query=db.query(Lead),
            cursor_field="created_at",
            cursor_value=None,
            limit=50
        )

        # Next page (using last item's created_at)
        last_cursor = leads[-1].created_at
        next_leads = paginate_cursor(
            query=db.query(Lead),
            cursor_field="created_at",
            cursor_value=last_cursor,
            limit=50
        )
    """
    from sqlalchemy import desc, asc

    # Get the model's column
    model = query.column_descriptions[0]['type']
    cursor_column = getattr(model, cursor_field)

    # Apply cursor filter if provided
    if cursor_value is not None:
        if order.lower() == "desc":
            query = query.filter(cursor_column < cursor_value)
        else:
            query = query.filter(cursor_column > cursor_value)

    # Apply ordering
    if order.lower() == "desc":
        query = query.order_by(desc(cursor_column))
    else:
        query = query.order_by(asc(cursor_column))

    # Apply limit
    results = query.limit(limit).all()

    return results


def extract_pagination_params(request_args: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract and validate pagination parameters from request.

    Args:
        request_args: Flask request.args dictionary

    Returns:
        dict: Validated pagination parameters
            {
                "page": int,
                "per_page": int,
                "cursor": str or None
            }

    Example:
        from flask import request
        params = extract_pagination_params(request.args)
        results, total = paginate_query(query, **params)
    """
    # Extract page parameter
    try:
        page = int(request_args.get("page", 1))
        page = max(1, page)  # Minimum 1
    except (ValueError, TypeError):
        page = 1

    # Extract per_page parameter
    try:
        per_page = int(request_args.get("per_page", 50))
        per_page = min(max(1, per_page), 100)  # Between 1 and 100
    except (ValueError, TypeError):
        per_page = 50

    # Extract cursor parameter (for cursor-based pagination)
    cursor = request_args.get("cursor")

    return {
        "page": page,
        "per_page": per_page,
        "cursor": cursor
    }


def create_cursor_response(
    items: List[Any],
    cursor_field: str,
    limit: int,
    endpoint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standardized cursor-based pagination response.

    Args:
        items: List of result items
        cursor_field: Field used for cursor
        limit: Items per page
        endpoint: API endpoint path (optional)

    Returns:
        dict: Cursor-paginated response with metadata

    Example:
        response = create_cursor_response(
            items=leads,
            cursor_field="created_at",
            limit=50,
            endpoint="/api/leads"
        )
    """
    has_more = len(items) == limit
    next_cursor = None

    if has_more and items:
        # Get cursor value from last item
        last_item = items[-1]
        next_cursor = getattr(last_item, cursor_field)

        # Convert to string if it's a datetime
        from datetime import datetime
        if isinstance(next_cursor, datetime):
            next_cursor = next_cursor.isoformat()
        else:
            next_cursor = str(next_cursor)

    response = {
        "data": items,
        "pagination": {
            "cursor_field": cursor_field,
            "limit": limit,
            "has_more": has_more,
            "next_cursor": next_cursor
        }
    }

    # Add next URL if endpoint provided
    if endpoint and has_more and next_cursor:
        response["pagination"]["next_url"] = f"{endpoint}?cursor={next_cursor}&limit={limit}"

    return response


# Export public API
__all__ = [
    "paginate_query",
    "create_pagination_response",
    "paginate_cursor",
    "extract_pagination_params",
    "create_cursor_response"
]
