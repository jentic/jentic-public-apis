import os
import tempfile
import json
import shutil
import time
import unittest
from oak_runner.blob_store import InMemoryBlobStore, LocalFileBlobStore

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

if __name__ == "__main__":
    unittest.main() 