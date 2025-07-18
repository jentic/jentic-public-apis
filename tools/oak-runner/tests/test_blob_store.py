import os
import tempfile
import json
import shutil
import time
import unittest
from typing import Any

from oak_runner import OAKRunner, WorkflowExecutionStatus
from oak_runner.blob_store import InMemoryBlobStore, LocalFileBlobStore
from .base_test import ArazzoTestCase
from .mocks.http_client import MockResponse, RequestMatcher


class TestInMemoryBlobStore(unittest.TestCase):
    def test_load_nonexistent_blob_raises(self):
        store = InMemoryBlobStore()
        with self.assertRaises(FileNotFoundError):
            store.load("does-not-exist")

    def test_info_nonexistent_blob_raises(self):
        store = InMemoryBlobStore()
        with self.assertRaises(FileNotFoundError):
            store.info("does-not-exist")

    def test_delete_nonexistent_blob_noop(self):
        store = InMemoryBlobStore()
        # Should not raise
        store.delete("does-not-exist")

    def test_lru_eviction(self):
        store = InMemoryBlobStore(max_size=2)
        id1 = store.save(b"data1", {"meta": 1})
        id2 = store.save(b"data2", {"meta": 2})
        # Both blobs present
        self.assertEqual(store.load(id1), b"data1")
        self.assertEqual(store.load(id2), b"data2")
        id3 = store.save(b"data3", {"meta": 3})
        # id1 should be evicted
        with self.assertRaises(FileNotFoundError):
            store.load(id1)
        self.assertEqual(store.load(id2), b"data2")
        self.assertEqual(store.load(id3), b"data3")

class TestLocalFileBlobStore(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.store = LocalFileBlobStore(root=self.tempdir, janitor_after_h=0.0001)  # ~0.36s

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_load_nonexistent_blob_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.store.load("does-not-exist")

    def test_info_nonexistent_blob_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.store.info("does-not-exist")

    def test_delete_nonexistent_blob_noop(self):
        # Should not raise
        self.store.delete("does-not-exist")

    def test_purge_old_deletes_old_blobs(self):
        # Save two blobs, one old, one new
        id_old = self.store.save(b"old", {"meta": "old"})
        id_new = self.store.save(b"new", {"meta": "new"})
        # Manually set old blob's ts to far in the past
        meta_path = self.store._meta_path(id_old)
        with open(meta_path, "r+") as f:
            meta = json.load(f)
            meta["ts"] = time.time() - 3600  # 1 hour ago
            f.seek(0)
            json.dump(meta, f)
            f.truncate()
        # New blob's ts is now
        self.store.purge_old()
        # Old blob should be gone
        with self.assertRaises(FileNotFoundError):
            self.store.load(id_old)
        # New blob should remain
        self.assertEqual(self.store.load(id_new), b"new")

    def test_purge_old_handles_corrupt_metadata(self):
        # Save a valid blob
        id_valid = self.store.save(b"valid", {"meta": "valid"})
        # Create a corrupt .json file
        corrupt_path = os.path.join(self.tempdir, "corrupt.json")
        with open(corrupt_path, "w") as f:
            f.write("not a json")
        # Should not raise, should log a warning
        self.store.purge_old()
        # Valid blob should remain
        self.assertEqual(self.store.load(id_valid), b"valid")

    def test_purge_old_handles_missing_metadata(self):
        # Create a .json file, then delete it before purge
        id_blob = self.store.save(b"blob", {"meta": "blob"})
        meta_path = self.store._meta_path(id_blob)
        os.remove(meta_path)
        # Should not raise
        self.store.purge_old()
        # The .bin file may remain, but info/load should now fail
        with self.assertRaises(FileNotFoundError):
            self.store.info(id_blob)


class TestBlobLogicInWorkflow(ArazzoTestCase):
    """Workflow-level blob logic tests."""

    def test_large_binary_not_stored_in_workflow(self):  # noqa: C901 – fine for test
        # ------------------------------------------------------------------
        # 1. Minimal OpenAPI spec
        # ------------------------------------------------------------------
        openapi_spec: dict[str, Any] = {
            "openapi": "3.0.0",
            "info": {"title": "Blob API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com/v1"}],
            "paths": {
                "/binary": {
                    "get": {
                        "operationId": "getBinary",
                        "responses": {
                            "200": {
                                "description": "binary data",
                                "content": {
                                    "audio/mpeg": {
                                        "schema": {"type": "string", "format": "binary"}
                                    }
                                },
                            }
                        },
                    }
                },
                "/upload": {
                    "post": {
                        "operationId": "uploadFile",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "file": {"type": "string", "format": "binary"}
                                        },
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"status": {"type": "string"}},
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
            },
        }

        openapi_path = self.create_openapi_spec(openapi_spec, "blob_api")

        # ------------------------------------------------------------------
        # 2. Arazzo workflow
        # ------------------------------------------------------------------
        arazzo_workflow: dict[str, Any] = {
            "workflowId": "binaryWorkflow",
            "summary": "Fetch binary and upload",
            "inputs": {"type": "object", "properties": {}},
            "steps": [
                {
                    "stepId": "fetchBinary",
                    "operationId": "getBinary",
                    "successCriteria": [{"condition": "$statusCode == 200"}],
                    "outputs": {"audio": "$response.body"},
                },
                {
                    "stepId": "sendBinary",
                    "operationId": "uploadFile",
                    "requestBody": {
                        "contentType": "multipart/form-data",
                        "payload": {"file": "$steps.fetchBinary.outputs.audio"},
                    },
                    "successCriteria": [{"condition": "$statusCode == 200"}],
                    "outputs": {"status": "$response.body#/status"},
                },
            ],
            "outputs": {"status": "$steps.sendBinary.outputs.status"},
        }

        arazzo_spec: dict[str, Any] = {
            "arazzo": "1.0.0",
            "info": {"title": "Blob Workflow", "version": "1.0.0"},
            "sourceDescriptions": [
                {"name": "blobApi", "url": openapi_path, "type": "openapi"}
            ],
            "workflows": [arazzo_workflow],
        }

        arazzo_doc = self.create_arazzo_spec(arazzo_spec, "blob_workflow")

        # ------------------------------------------------------------------
        # 3. Mock HTTP responses
        # ------------------------------------------------------------------
        large_binary = os.urandom(50_000)  # 50 KiB

        # GET /binary returns large binary
        self.http_client.add_matcher(
            RequestMatcher("GET", "https://api.example.com/v1/binary"),
            MockResponse(200, headers={"Content-Type": "audio/mpeg"}, content=large_binary),
        )

        # POST /upload returns JSON {"status": "ok"}
        self.http_client.add_static_response(
            "POST",
            "https://api.example.com/v1/upload",
            status_code=200,
            json_data={"status": "ok"},
            headers={"Content-Type": "application/json"},
        )

        # ------------------------------------------------------------------
        # 4. Execute workflow with blob store attached
        # ------------------------------------------------------------------
        blob_store = InMemoryBlobStore()
        runner = OAKRunner(
            arazzo_doc=arazzo_doc,
            source_descriptions={"blobApi": openapi_spec},
            http_client=self.http_client,
            blob_store=blob_store,
        )

        result = self.execute_workflow(runner, "binaryWorkflow", inputs={})

        # ------------------------------------------------------------------
        # 5. Assertions
        # ------------------------------------------------------------------
        self.assertEqual(
            result.status,
            WorkflowExecutionStatus.WORKFLOW_COMPLETE,
            "Workflow should complete successfully",
        )

        # Blob store should still be empty (no intermediate storage)
        self.assertEqual(
            len(blob_store.blobs),
            0,
            "Blob store must remain empty for intermediate steps",
        )

        # First step output should be raw bytes
        audio_bytes = result.step_outputs["fetchBinary"]["audio"]  # type: ignore[index]
        self.assertIsInstance(audio_bytes, (bytes, bytearray))
        self.assertEqual(
            len(audio_bytes),
            len(large_binary),
            "Uploaded bytes length mismatch",
        )

        # Two HTTP calls should have been made
        self.validate_api_calls(expected_call_count=2)


if __name__ == "__main__":
    unittest.main() 