# -*- coding: utf-8 -*-
"""Cloudflare R2 storage service."""
from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.client import Config

import config

logger = logging.getLogger(__name__)


class R2StorageService:
    """Handle uploads to Cloudflare R2."""

    _client = None

    @classmethod
    def _get_client(cls):
        """Create or reuse the boto3 S3-compatible client for R2."""
        if cls._client is not None:
            return cls._client

        required = [
            config.R2_ENDPOINT_URL,
            config.R2_ACCESS_KEY_ID,
            config.R2_SECRET_ACCESS_KEY,
            config.R2_BUCKET_NAME,
        ]
        if not all(required):
            missing = [
                name
                for name, value in [
                    ("R2_ENDPOINT_URL", config.R2_ENDPOINT_URL),
                    ("R2_ACCESS_KEY_ID", config.R2_ACCESS_KEY_ID),
                    ("R2_SECRET_ACCESS_KEY", config.R2_SECRET_ACCESS_KEY),
                    ("R2_BUCKET_NAME", config.R2_BUCKET_NAME),
                ]
                if not value
            ]
            raise RuntimeError(
                f"Cloudflare R2 未正确配置，缺少: {', '.join(missing)}"
            )

        session = boto3.session.Session()
        cls._client = session.client(
            "s3",
            region_name=config.R2_REGION or "auto",
            endpoint_url=config.R2_ENDPOINT_URL,
            aws_access_key_id=config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )
        return cls._client

    @classmethod
    def upload_image(
        cls,
        file_stream,
        filename: str,
        content_type: Optional[str] = None,
        folder: str = "uploads/images",
    ) -> dict:
        """Upload an image file to R2 and return metadata."""
        client = cls._get_client()

        content_type = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        if not content_type.startswith("image"):
            raise ValueError("仅支持上传图片文件")

        ext = os.path.splitext(filename)[1] or mimetypes.guess_extension(content_type) or ""
        ext = ext.lstrip(".")
        unique_name = f"{uuid.uuid4().hex}{f'.{ext}' if ext else ''}"
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        key = f"{folder}/{date_path}/{unique_name}".replace("//", "/")

        extra_args = {
            "ContentType": content_type,
        }

        client.upload_fileobj(file_stream, config.R2_BUCKET_NAME, key, ExtraArgs=extra_args)

        if config.R2_PUBLIC_URL:
            public_url = f"{config.R2_PUBLIC_URL.rstrip('/')}/{key}"
        else:
            public_url = f"{config.R2_ENDPOINT_URL.rstrip('/')}/{config.R2_BUCKET_NAME}/{key}"

        logger.info("上传文件到R2: bucket=%s key=%s", config.R2_BUCKET_NAME, key)

        return {
            "bucket": config.R2_BUCKET_NAME,
            "key": key,
            "url": public_url,
            "content_type": content_type,
        }
