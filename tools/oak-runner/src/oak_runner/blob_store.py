#!/usr/bin/env python3
"""
Blob Storage for OAK Runner

This module provides blob storage functionality to handle binary data
without cluttering JSON payloads and LLM context.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Protocol

# Configure logging
logger = logging.getLogger("arazzo-runner.blob_store")


class BlobStore(Protocol):
    """Protocol for blob storage backends."""
    
    def save(self, data: bytes, meta: dict[str, Any]) -> str:
        """Save binary data and return a blob ID."""
        ...
    
    def load(self, blob_id: str) -> bytes:
        """Load binary data by blob ID."""
        ...
    
    def info(self, blob_id: str) -> dict[str, Any]:
        """Get metadata for a blob."""
        ...
    
    def delete(self, blob_id: str) -> None:
        """Delete a blob by ID."""
        ...


class LocalFileBlobStore:
    """File-based blob storage implementation."""
    
    def __init__(self, root: str | None = None, janitor_after_h: int = 24):
        """
        Initialize the local file blob store.
        
        Args:
            root: Root directory for blob storage (defaults to env BLOB_STORE_PATH or CWD/blobs).            janitor_after_h: Number of hours after which blobs are eligible for cleanup
        """
        # The temp dir might suit this better, but I don't want to assume OS.
        self.root = root or os.getenv("BLOB_STORE_PATH", os.path.join(os.getcwd(), "blobs"))
        self.janitor_after = janitor_after_h * 3600
        
        # Create the storage directory if it doesn't exist
        os.makedirs(self.root, exist_ok=True)
        logger.debug(f"Initialized blob store at {self.root}")
    
    def _path(self, blob_id: str) -> str:
        """Get the file path for a blob's binary data."""
        return os.path.join(self.root, f"{blob_id}.bin")
    
    def _meta_path(self, blob_id: str) -> str:
        """Get the file path for a blob's metadata."""
        return os.path.join(self.root, f"{blob_id}.json")
    
    def save(self, data: bytes, meta: dict[str, Any]) -> str:
        """
        Save binary data with metadata.
        
        Args:
            data: Binary data to store
            meta: Metadata dictionary
            
        Returns:
            Unique blob ID for the stored data
        """
        blob_id = str(uuid.uuid4())
        
        # Save binary data
        with open(self._path(blob_id), "wb") as f:
            f.write(data)
        
        # Save metadata with timestamp
        meta_with_ts = meta.copy()
        meta_with_ts["ts"] = time.time()
        meta_with_ts["size"] = len(data)
        
        with open(self._meta_path(blob_id), "w") as f:
            json.dump(meta_with_ts, f)
        
        logger.debug(f"Stored blob {blob_id} ({len(data)} bytes)")
        return blob_id
    
    def load(self, blob_id: str) -> bytes:
        """
        Load binary data by blob ID.
        
        Args:
            blob_id: The blob ID to load
            
        Returns:
            Binary data
            
        Raises:
            FileNotFoundError: If the blob doesn't exist
        """
        blob_path = self._path(blob_id)
        if not os.path.exists(blob_path):
            raise FileNotFoundError(f"Blob {blob_id} not found")
        
        with open(blob_path, "rb") as f:
            data = f.read()
        
        logger.debug(f"Loaded blob {blob_id} ({len(data)} bytes)")
        return data
    
    def info(self, blob_id: str) -> dict[str, Any]:
        """
        Get metadata for a blob.
        
        Args:
            blob_id: The blob ID
            
        Returns:
            Metadata dictionary
            
        Raises:
            FileNotFoundError: If the blob doesn't exist
        """
        meta_path = self._meta_path(blob_id)
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Blob {blob_id} metadata not found")
        
        with open(meta_path) as f:
            return json.load(f)
    
    def delete(self, blob_id: str) -> None:
        """
        Delete a blob and its metadata.
        
        Args:
            blob_id: The blob ID to delete
        """
        for path in (self._path(blob_id), self._meta_path(blob_id)):
            if os.path.exists(path):
                os.remove(path)
                logger.debug(f"Deleted {path}")
    
    def purge_old(self) -> None:
        """Remove blobs older than the janitor threshold."""
        threshold = time.time() - self.janitor_after
        purged_count = 0
        
        try:
            for fname in os.listdir(self.root):
                if fname.endswith(".json"):
                    meta_path = os.path.join(self.root, fname)
                    try:
                        with open(meta_path) as f:
                            meta = json.load(f)
                        
                        if meta.get("ts", 0) < threshold:
                            blob_id = fname[:-5]  # strip .json
                            self.delete(blob_id)
                            purged_count += 1
                    except (json.JSONDecodeError, OSError) as e:
                        logger.warning(f"Error processing {meta_path}: {e}")
            
            if purged_count > 0:
                logger.info(f"Purged {purged_count} old blobs")
        except OSError as e:
            logger.warning(f"Error during purge: {e}")


class InMemoryBlobStore:
    """In-memory blob storage for testing and short-lived scenarios."""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize in-memory blob store.
        
        Args:
            max_size: Maximum number of blobs to keep in memory
        """
        self.blobs: dict[str, bytes] = {}
        self.metadata: dict[str, dict[str, Any]] = {}
        self.max_size = max_size
        self.access_order: list[str] = []  # For LRU eviction
    
    def _evict_if_needed(self) -> None:
        """Evict oldest blobs if we've exceeded max_size."""
        while len(self.blobs) >= self.max_size and self.access_order:
            oldest_id = self.access_order.pop(0)
            self.blobs.pop(oldest_id, None)
            self.metadata.pop(oldest_id, None)
    
    def save(self, data: bytes, meta: dict[str, Any]) -> str:
        """Save binary data with metadata."""
        self._evict_if_needed()
        
        blob_id = str(uuid.uuid4())
        self.blobs[blob_id] = data
        
        meta_with_ts = meta.copy()
        meta_with_ts["ts"] = time.time()
        meta_with_ts["size"] = len(data)
        self.metadata[blob_id] = meta_with_ts
        
        self.access_order.append(blob_id)
        return blob_id
    
    def load(self, blob_id: str) -> bytes:
        """Load binary data by blob ID."""
        if blob_id not in self.blobs:
            raise FileNotFoundError(f"Blob {blob_id} not found")
        
        # Update access order for LRU
        if blob_id in self.access_order:
            self.access_order.remove(blob_id)
        self.access_order.append(blob_id)
        
        return self.blobs[blob_id]
    
    def info(self, blob_id: str) -> dict[str, Any]:
        """Get metadata for a blob."""
        if blob_id not in self.metadata:
            raise FileNotFoundError(f"Blob {blob_id} metadata not found")
        return self.metadata[blob_id].copy()
    
    def delete(self, blob_id: str) -> None:
        """Delete a blob and its metadata."""
        self.blobs.pop(blob_id, None)
        self.metadata.pop(blob_id, None)
        if blob_id in self.access_order:
            self.access_order.remove(blob_id)

 