import pytest
from oak_runner.http import HTTPExecutor
from oak_runner.blob_store import InMemoryBlobStore


class MockCredentialProvider:
    """Mock credential provider for testing - ONLY mock out what we need"""

    def get_credentials(self, security_options, fetch_options):
        """Mock implementation of get_credentials"""
        return []


@pytest.fixture
def basic_http_client() -> HTTPExecutor:
    """HTTP client without auth provider for basic tests"""
    return HTTPExecutor(blob_store=InMemoryBlobStore())


@pytest.fixture  
def http_client() -> HTTPExecutor:
    """HTTP client with mock auth provider and in-memory blob store for tests"""
    return HTTPExecutor(
        auth_provider=MockCredentialProvider(),
        blob_store=InMemoryBlobStore()
    ) 