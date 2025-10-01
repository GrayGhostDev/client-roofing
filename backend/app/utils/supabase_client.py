"""
iSwitch Roofs CRM - Supabase Client Integration
Version: 1.0.0
Date: 2025-10-01
"""

from supabase import create_client, Client
from flask import current_app, g
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """
    Get Supabase client instance (singleton per request).

    Returns:
        Client: Supabase client instance

    Raises:
        ValueError: If Supabase credentials are not configured
    """
    if "supabase" not in g:
        url = current_app.config.get("SUPABASE_URL")
        key = current_app.config.get("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("Supabase URL and KEY must be configured")

        g.supabase = create_client(url, key)
        logger.debug("Created new Supabase client instance")

    return g.supabase


def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client instance with service role key.
    Use this for server-side operations that bypass RLS.

    Returns:
        Client: Supabase admin client instance

    Raises:
        ValueError: If Supabase credentials are not configured
    """
    if "supabase_admin" not in g:
        url = current_app.config.get("SUPABASE_URL")
        service_key = current_app.config.get("SUPABASE_SERVICE_KEY")

        if not url or not service_key:
            raise ValueError("Supabase URL and SERVICE_KEY must be configured")

        g.supabase_admin = create_client(url, service_key)
        logger.debug("Created new Supabase admin client instance")

    return g.supabase_admin


class SupabaseService:
    """
    Service class for Supabase database operations.
    Provides a high-level interface for common database operations.
    """

    def __init__(self, use_admin=False):
        """
        Initialize Supabase service.

        Args:
            use_admin (bool): Whether to use admin client (bypasses RLS)
        """
        self.client = get_supabase_admin_client() if use_admin else get_supabase_client()

    def select(self, table: str, columns: str = "*", **filters):
        """
        Select records from a table.

        Args:
            table (str): Table name
            columns (str): Columns to select (default: "*")
            **filters: Filter conditions (e.g., status='active')

        Returns:
            list: List of matching records
        """
        try:
            query = self.client.table(table).select(columns)

            for key, value in filters.items():
                query = query.eq(key, value)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error selecting from {table}: {str(e)}")
            raise

    def select_one(self, table: str, id_value: str, id_column: str = "id", columns: str = "*"):
        """
        Select a single record by ID.

        Args:
            table (str): Table name
            id_value (str): ID value
            id_column (str): ID column name (default: "id")
            columns (str): Columns to select (default: "*")

        Returns:
            dict: Record data or None if not found
        """
        try:
            response = self.client.table(table).select(columns).eq(id_column, id_value).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error selecting {id_value} from {table}: {str(e)}")
            return None

    def insert(self, table: str, data: dict):
        """
        Insert a record into a table.

        Args:
            table (str): Table name
            data (dict): Record data

        Returns:
            dict: Inserted record with generated fields
        """
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error inserting into {table}: {str(e)}")
            raise

    def insert_many(self, table: str, data: list):
        """
        Insert multiple records into a table.

        Args:
            table (str): Table name
            data (list): List of record dictionaries

        Returns:
            list: Inserted records
        """
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error bulk inserting into {table}: {str(e)}")
            raise

    def update(self, table: str, id_value: str, data: dict, id_column: str = "id"):
        """
        Update a record by ID.

        Args:
            table (str): Table name
            id_value (str): ID value
            data (dict): Update data
            id_column (str): ID column name (default: "id")

        Returns:
            dict: Updated record
        """
        try:
            response = self.client.table(table).update(data).eq(id_column, id_value).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating {id_value} in {table}: {str(e)}")
            raise

    def delete(self, table: str, id_value: str, id_column: str = "id"):
        """
        Delete a record by ID.

        Args:
            table (str): Table name
            id_value (str): ID value
            id_column (str): ID column name (default: "id")

        Returns:
            dict: Deleted record
        """
        try:
            response = self.client.table(table).delete().eq(id_column, id_value).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error deleting {id_value} from {table}: {str(e)}")
            raise

    def count(self, table: str, **filters):
        """
        Count records in a table.

        Args:
            table (str): Table name
            **filters: Filter conditions

        Returns:
            int: Number of matching records
        """
        try:
            query = self.client.table(table).select("*", count="exact")

            for key, value in filters.items():
                query = query.eq(key, value)

            response = query.execute()
            return response.count
        except Exception as e:
            logger.error(f"Error counting records in {table}: {str(e)}")
            raise

    def search(self, table: str, column: str, search_term: str, columns: str = "*"):
        """
        Search records using text search.

        Args:
            table (str): Table name
            column (str): Column to search
            search_term (str): Search term
            columns (str): Columns to select (default: "*")

        Returns:
            list: Matching records
        """
        try:
            response = (
                self.client.table(table)
                .select(columns)
                .ilike(column, f"%{search_term}%")
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error searching {table}: {str(e)}")
            raise

    def execute_rpc(self, function_name: str, params: Optional[dict] = None):
        """
        Execute a Supabase RPC (stored procedure/function).

        Args:
            function_name (str): Name of the database function
            params (dict, optional): Function parameters

        Returns:
            Any: Function result
        """
        try:
            response = self.client.rpc(function_name, params or {}).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error executing RPC {function_name}: {str(e)}")
            raise

    def upload_file(self, bucket: str, path: str, file_data: bytes, content_type: str = None):
        """
        Upload a file to Supabase storage.

        Args:
            bucket (str): Storage bucket name
            path (str): File path in bucket
            file_data (bytes): File data
            content_type (str, optional): Content type

        Returns:
            str: Public URL of uploaded file
        """
        try:
            options = {}
            if content_type:
                options["content-type"] = content_type

            self.client.storage.from_(bucket).upload(path, file_data, file_options=options)

            # Get public URL
            url = self.client.storage.from_(bucket).get_public_url(path)
            return url
        except Exception as e:
            logger.error(f"Error uploading file to {bucket}/{path}: {str(e)}")
            raise

    def delete_file(self, bucket: str, path: str):
        """
        Delete a file from Supabase storage.

        Args:
            bucket (str): Storage bucket name
            path (str): File path in bucket

        Returns:
            bool: True if deleted successfully
        """
        try:
            self.client.storage.from_(bucket).remove([path])
            return True
        except Exception as e:
            logger.error(f"Error deleting file from {bucket}/{path}: {str(e)}")
            raise


def init_storage_buckets():
    """
    Initialize Supabase storage buckets if they don't exist.
    Should be called during application setup.
    """
    try:
        admin_client = get_supabase_admin_client()

        # Define buckets
        buckets = [
            {"name": "before-photos", "public": False},
            {"name": "after-photos", "public": True},
            {"name": "documents", "public": False},
            {"name": "contracts", "public": False},
            {"name": "invoices", "public": False},
        ]

        existing_buckets = admin_client.storage.list_buckets()
        existing_names = {bucket["name"] for bucket in existing_buckets}

        for bucket in buckets:
            if bucket["name"] not in existing_names:
                admin_client.storage.create_bucket(bucket["name"], {"public": bucket["public"]})
                logger.info(f"Created storage bucket: {bucket['name']}")

    except Exception as e:
        logger.error(f"Error initializing storage buckets: {str(e)}")
