"""Supabase Storage adapter untuk export pack.

Catatan:
- Service role key wajib server-side; tidak boleh dibocorkan ke client (Vite).
- Akses bucket private hanya lewat signed URL berbasis TTL (lihat settings).
- Jika supabase_url / supabase_service_role_key kosong, adapter beroperasi
  sebagai no-op sehingga endpoint export tetap berjalan di mode dev/lokal.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.settings import get_settings


@dataclass
class SignedUrlResult:
    bucket: str
    path: str
    signed_url: str | None
    expires_in_seconds: int


class SupabaseStorageAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.supabase_url
        self.service_role_key = settings.supabase_service_role_key
        self.default_ttl = settings.export_signed_url_ttl_seconds
        self.exports_bucket = settings.supabase_exports_bucket
        self.uploads_bucket = settings.supabase_uploads_bucket

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.service_role_key)

    async def create_signed_url(
        self,
        bucket: str,
        path: str,
        ttl_seconds: int | None = None,
    ) -> SignedUrlResult:
        ttl = ttl_seconds or self.default_ttl
        if not self.configured:
            return SignedUrlResult(bucket=bucket, path=path, signed_url=None, expires_in_seconds=ttl)
        url = f"{self.base_url}/storage/v1/object/sign/{bucket}/{path}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"expiresIn": ttl}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        signed_path = data.get("signedURL") or data.get("signed_url")
        signed_url = f"{self.base_url}/storage/v1{signed_path}" if signed_path else None
        return SignedUrlResult(bucket=bucket, path=path, signed_url=signed_url, expires_in_seconds=ttl)

    async def upload_object(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        upsert: bool = True,
    ) -> bool:
        if not self.configured:
            return False
        url = f"{self.base_url}/storage/v1/object/{bucket}/{path}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": content_type,
            "x-upsert": "true" if upsert else "false",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, content=content, headers=headers)
            resp.raise_for_status()
        return True
