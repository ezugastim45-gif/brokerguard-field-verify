"""Supabase client for file uploads and database operations."""

from supabase import create_client, Client
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid

from .config import settings


class SupabaseClient:
    """Client for Supabase operations."""

    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key  # Use service role for backend
        )
        self.bucket_name = settings.supabase_bucket

    def upload_file(
        self,
        file_path: str,
        destination_path: str,
        content_type: str = "image/png"
    ) -> str:
        """
        Uploads file to Supabase Storage.

        Args:
            file_path: Local path to file
            destination_path: Remote path in bucket (e.g., "images/2026-05/abc123.png")
            content_type: MIME type

        Returns:
            Public URL of uploaded file

        Raises:
            Exception: If upload fails
        """
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Upload to storage
        response = self.client.storage.from_(self.bucket_name).upload(
            path=destination_path,
            file=file_data,
            file_options={"content-type": content_type}
        )

        # Get public URL
        public_url = self.client.storage.from_(self.bucket_name).get_public_url(destination_path)

        return public_url

    def insert_verification(
        self,
        broker_id: str,
        property_id: str,
        lat: float,
        lon: float,
        altitude: Optional[float],
        address: str,
        image_hash: str,
        stamped_image_url: str,
        pdf_url: Optional[str],
        verified_at: datetime,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Inserts verification record into database.

        Args:
            broker_id: Broker UUID
            property_id: Property identifier
            lat: Latitude
            lon: Longitude
            altitude: Altitude in meters
            address: Human-readable address
            image_hash: SHA-256 hash
            stamped_image_url: URL of stamped image
            pdf_url: URL of PDF report
            verified_at: Timestamp of verification
            metadata: Additional metadata (JSONB)

        Returns:
            Inserted record

        Raises:
            Exception: If insert fails
        """
        data = {
            "broker_id": broker_id,
            "property_id": property_id,
            "lat": lat,
            "lon": lon,
            "altitude": altitude,
            "address": address,
            "image_hash": image_hash,
            "stamped_image_url": stamped_image_url,
            "pdf_url": pdf_url,
            "verified_at": verified_at.isoformat(),
            "metadata": metadata
        }

        response = self.client.table("field_verifications").insert(data).execute()

        if response.data:
            return response.data[0]
        else:
            raise Exception(f"Failed to insert verification: {response}")

    def get_verification_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves verification by hash.

        Args:
            image_hash: SHA-256 hash to lookup

        Returns:
            Verification record or None if not found
        """
        response = self.client.table("field_verifications").select("*").eq(
            "image_hash", image_hash
        ).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    def get_verifications_by_broker(
        self,
        broker_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[Dict[str, Any]]:
        """
        Retrieves verifications for a broker.

        Args:
            broker_id: Broker UUID
            limit: Max results to return
            offset: Pagination offset

        Returns:
            List of verification records
        """
        response = self.client.table("field_verifications").select("*").eq(
            "broker_id", broker_id
        ).order("verified_at", desc=True).limit(limit).offset(offset).execute()

        return response.data if response.data else []

    def get_verifications_by_property(
        self,
        property_id: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieves verifications for a property.

        Args:
            property_id: Property identifier
            limit: Max results to return

        Returns:
            List of verification records
        """
        response = self.client.table("field_verifications").select("*").eq(
            "property_id", property_id
        ).order("verified_at", desc=True).limit(limit).execute()

        return response.data if response.data else []

    def generate_storage_path(self, hash_value: str, file_extension: str, timestamp: datetime) -> str:
        """
        Generates storage path with year-month organization.

        Args:
            hash_value: SHA-256 hash
            file_extension: File extension (png, jpg, pdf)
            timestamp: Timestamp for date-based organization

        Returns:
            Storage path like "images/2026-05/abc123.png"
        """
        year_month = timestamp.strftime("%Y-%m")

        if file_extension in ["png", "jpg", "jpeg"]:
            folder = "images"
        elif file_extension == "pdf":
            folder = "pdfs"
        else:
            folder = "files"

        return f"{folder}/{year_month}/{hash_value}.{file_extension}"


# Singleton instance
supabase_client = SupabaseClient()
