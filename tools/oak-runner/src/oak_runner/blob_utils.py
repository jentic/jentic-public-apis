#!/usr/bin/env python3
"""
Blob Storage Utilities for OAK Runner

This module provides helper functions for handling blob storage.
"""
import logging
import os
from typing import Any
import requests

from .blob_store import BlobStore

# Configure logging
logger = logging.getLogger("arazzo-runner.blob_utils")


def should_store_as_blob(
    content_type: str, size: int, blob_threshold: int, is_binary: bool
) -> bool:
    """
    Determine if response content should be stored as a blob.

    Args:
        content_type: The response Content-Type header
        size: Size of the response content in bytes
        blob_threshold: Size threshold for blob storage
        is_binary: Whether the content is considered binary

    Returns:
        True if content should be stored as blob, False otherwise
    """
    if is_binary:
        return True

    return size > blob_threshold


def analyze_response_for_blob(response: requests.Response, is_binary: bool) -> dict:
    """
    Analyze if response content should be stored as a blob.
    This method only analyzes and provides metadata - it does not store anything.

    Args:
        response: The HTTP response object from `requests` library
        is_binary: Pre-determined flag indicating if the content is binary

    Returns:
        Dictionary with blob analysis metadata
    """
    content_type = response.headers.get("Content-Type", "")
    size = len(response.content)

    # Default blob threshold for analysis (can be overridden by workflow layer)
    blob_threshold = int(os.environ.get("ARAZZO_BLOB_THRESHOLD", "32768"))  # 32KB

    should_store = should_store_as_blob(content_type, size, blob_threshold, is_binary)

    return {
        "should_store": should_store,
        "content_type": content_type,
        "size": size,
        "is_binary": is_binary,
    }


def maybe_store_response_as_blob(blob_store: BlobStore, response: dict, step_id: str) -> dict:
    """
    Handle blob storage for response if blob_store is available and appropriate.

    Args:
        blob_store: The blob store instance for saving data.
        response: Response from HTTPExecutor containing body and blob_metadata.
        step_id: ID of the current step for logging.

    Returns:
        Updated response with blob reference if stored, original response otherwise.
    """
    if not blob_store:
        return response

    blob_metadata = response.get("blob_metadata", {})
    if not blob_metadata.get("should_store", False):
        return response

    # Store the response body as a blob
    try:
        metadata = {
            "content_type": blob_metadata.get("content_type", ""),
            "size": blob_metadata.get("size", 0),
            "step_id": step_id,
            "status_code": response.get("status_code", 0),
        }

        blob_id = blob_store.save(response["body"], metadata)

        logger.info(
            f"Stored response as blob {blob_id} for step {step_id} "
            f"({blob_metadata.get('size', 0)} bytes, {blob_metadata.get('content_type', 'unknown')})"
        )

        # Replace body with blob reference
        response_copy = response.copy()
        response_copy["body"] = {
            "blob_ref": blob_id,
            "content_type": blob_metadata.get("content_type", ""),
            "size": blob_metadata.get("size", 0),
        }

        return response_copy

    except Exception as e:
        logger.error(f"Failed to store blob for step {step_id}: {e}")
        return response 