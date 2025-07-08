#!/usr/bin/env python3
"""
Tests for the HTTP Client in OAK Runner

This file contains tests for the HTTPExecutor class in the OAK Runner library,
with a focus on authentication handling.
"""
import pytest
from unittest.mock import Mock
import logging

from oak_runner.auth.credentials.models import Credential
import requests
from unittest.mock import patch, MagicMock
from oak_runner.auth.models import SecurityOption, SecurityRequirement, RequestAuthValue, AuthLocation
from oak_runner.http import HTTPExecutor
from oak_runner.blob_store import InMemoryBlobStore

logger = logging.getLogger(__name__)

class MockCredentialProvider:
    """Mock credential provider for testing - ONLY mock out what we need"""

    def get_credentials(self, security_options, fetch_options):
        """Mock implementation of get_credentials"""
        return []


@pytest.fixture
def basic_http_client() -> HTTPExecutor:
    return HTTPExecutor()


@pytest.fixture
def http_client() -> HTTPExecutor:
    return HTTPExecutor(auth_provider=MockCredentialProvider())


def test_init(basic_http_client: HTTPExecutor):
    """Test that the HTTP client initializes correctly"""
    assert basic_http_client is not None
    assert basic_http_client.auth_provider is None


def test_apply_auth_no_provider(basic_http_client: HTTPExecutor):
    """Test that auth application is skipped when no auth provider is available"""
    headers = {}
    query_params = {}
    cookies = {}

    # No auth provider set
    basic_http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies
    )

    # Should not modify any of the dictionaries
    assert headers == {}
    assert query_params == {}
    assert cookies == {}


def test_apply_auth_query_parameter(http_client: HTTPExecutor):
    """Test applying auth as query parameters"""
    # Mock out the get_credentials to return a credential
    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="test-credential-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.QUERY,
                    name="api-key",
                    auth_value="test-api-key-12345"
                )
            )
        ]
    )

    headers = {}
    query_params = {}
    cookies = {}

    # Create security options
    security_options = [
        SecurityOption(
            requirements=[
                SecurityRequirement(scheme_name="api-key", scopes=[])
            ]
        )
    ]

    # Apply auth
    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    # Check that query parameters were updated correctly
    assert query_params == {"api-key": "test-api-key-12345"}
    # Headers and cookies should remain empty
    assert headers == {}
    assert cookies == {}


def test_apply_auth_header(http_client: HTTPExecutor):
    """Test applying auth as headers"""
    # Create mock auth provider with header auth
    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.HEADER,
                    name="X-Api-Key",
                    auth_value="test-api-key-12345"
                )
            )
        ]
    )
    headers = {}
    query_params = {}
    cookies = {}

    # Create security options
    security_options = [
        SecurityOption(
            requirements=[
                SecurityRequirement(scheme_name="X-Api-Key", scopes=[])
            ]
        )
    ]

    # Apply auth
    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    # Check that headers were updated correctly
    assert headers == {"X-Api-Key": "test-api-key-12345"}
    # Query params and cookies should remain empty
    assert query_params == {}
    assert cookies == {}


def test_apply_auth_cookie(http_client: HTTPExecutor):
    """Test applying auth as cookies"""

    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.COOKIE,
                    name="session",
                    auth_value="test-session-id-12345"
                )
            )
        ]
    )
    headers = {}
    query_params = {}
    cookies = {}

    # Create security options
    security_options = [
        SecurityOption(
            requirements=[
                SecurityRequirement(scheme_name="session", scopes=[])
            ]
        )
    ]

    # Apply auth
    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    # Check that cookies were updated correctly
    assert cookies == {"session": "test-session-id-12345"}
    # Headers and query params should remain empty
    assert headers == {}
    assert query_params == {}


def test_apply_auth_multiple_requirements(http_client: HTTPExecutor):
    """Test applying auth with multiple requirements in different locations"""
    # Create mock auth provider with multiple auth requirements

    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.QUERY,
                    name="api-key",
                    auth_value="test-api-key-12345"
                )
            ),
            Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.HEADER,
                    name="X-Client-Id",
                    auth_value="client-12345"
                )
            ),
            Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.COOKIE,
                    name="session",
                    auth_value="test-session-id-12345"
                )
            )
        ]
    )
    headers = {}
    query_params = {}
    cookies = {}

    # Create security options
    security_options = [
        SecurityOption(
            requirements=[
                SecurityRequirement(scheme_name="api-key", scopes=[]),
                SecurityRequirement(scheme_name="X-Client-Id", scopes=[]),
                SecurityRequirement(scheme_name="session", scopes=[]),
            ]
        )
    ]

    # Apply auth
    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    # Check that all parameters were updated correctly
    assert query_params == {"api-key": "test-api-key-12345"}
    assert headers == {"X-Client-Id": "client-12345"}
    assert cookies == {"session": "test-session-id-12345"}


def test_apply_auth_missing_value(http_client: HTTPExecutor):
    """Test handling of missing auth values"""
    # Create mock auth provider with auth requirement but missing value
    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="test-credential-auth-id",
                request_auth_value=None
            )
        ]
    )

    headers = {}
    query_params = {}
    cookies = {}

    # Create security options
    security_options = [
        SecurityOption(
            requirements=[
                SecurityRequirement(scheme_name="api-key", scopes=[])
            ]
        )
    ]

    # Apply auth
    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    # All dictionaries should remain empty
    assert headers == {}
    assert query_params == {}
    assert cookies == {}


@pytest.mark.skip("Was broken before, what should happen?")
def test_apply_auth_unknown_location(http_client: HTTPExecutor):
    """Test handling of unknown auth location (should default to header)"""
    # Create mock auth provider with unknown auth location
    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location="unknown",  # Invalid location - this doesnt pass pydantic validation
                    name="api-key",
                    auth_value="test-api-key-12345"
                )
            )
        ]
    )

    headers = {}
    query_params = {}
    cookies = {}

    # Create security options
    security_options = [
        SecurityOption(
            requirements=[
                SecurityRequirement(scheme_name="api-key", scopes=[])
            ]
        )
    ]

    # Apply auth
    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    # Should default to header
    assert headers == {"api-key": "test-api-key-12345"}
    assert query_params == {}
    assert cookies == {}


def mock_get_credentials(request, options) -> list[Credential]:
    logger.debug(f"Mock get_credentials called with options: {options}")
    cred1 = Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.QUERY,
                    name="api1-key",
                    auth_value="api1-key-value"
                )
            )
        
    cred2 = Credential(
                id="test-credential-auth-id",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.HEADER,
                    name="api2-key",
                    auth_value="api2-key-value"
                )
            )
        
    if options.source_name == "api1":
        return [cred1]
    elif options.source_name == "api2":
        return [cred2]
    else:
        return [cred1, cred2]


def test_apply_auth_multiple_apis(http_client: HTTPExecutor):
    """Test applying auth from multiple APIs"""
    # Create mock auth provider with multiple APIs
    http_client.auth_provider.get_credentials = Mock(side_effect=mock_get_credentials)

    headers = {}
    query_params = {}
    cookies = {}

    # Create security options
    security_options = [
        SecurityOption(
            requirements=[
                SecurityRequirement(scheme_name="api1-key", scopes=[]),
                SecurityRequirement(scheme_name="api2-key", scopes=[]),
            ]
        )
    ]

    # Apply auth
    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    # Both APIs' auth should be applied
    assert query_params == {"api1-key": "api1-key-value"}
    assert headers == {"api2-key": "api2-key-value"}
    assert cookies == {}


def test_execute_request_multipart(http_client: HTTPExecutor):
    """Test executing a multipart/form-data request."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.json.return_value = {'status': 'ok'}

    request_body = {
        "contentType": "multipart/form-data",
        "payload": {
            "file": {
                "content": b"file content",
                "filename": "test.txt",
                "contentType": "text/plain"
            },
            "description": "A test file"
        }
    }
        
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        http_client.execute_request(
            method="POST",
            url="http://test.com/upload",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['method'] == 'POST'
        assert kwargs['url'] == 'http://test.com/upload'
        assert 'files' in kwargs
        assert kwargs['files']['file'] == ('test.txt', b'file content', 'text/plain')
        assert 'data' in kwargs
        assert kwargs['data']['description'] == 'A test file'
        assert 'Content-Type' not in kwargs['headers']  # requests sets this for multipart


def test_execute_request_json_body(http_client: HTTPExecutor):
    """Test executing a request with a JSON body."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.json.return_value = {'status': 'ok'}
    
    request_body = {
        "contentType": "application/json",
        "payload": {"key": "value"}
    }

    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        http_client.execute_request(
            method="POST",
            url="http://test.com/data",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )
        
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['json'] == {"key": "value"}
        assert kwargs['headers']['Content-Type'] == 'application/json'


def test_execute_request_form_body(http_client: HTTPExecutor):
    """Test executing a request with a form URL encoded body."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.side_effect = ValueError # no json
    mock_response.text = "Success"
    
    request_body = {
        "contentType": "application/x-www-form-urlencoded",
        "payload": {"key": "value"}
    }

    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        http_client.execute_request(
            method="POST",
            url="http://test.com/submit",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['data'] == {"key": "value"}
        assert kwargs['headers']['Content-Type'] == 'application/x-www-form-urlencoded'


def test_execute_request_raw_body(http_client: HTTPExecutor):
    """Test executing a request with a raw string body."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.side_effect = ValueError
    mock_response.text = "OK"
    
    request_body = {
        "contentType": "text/plain",
        "payload": "this is raw text"
    }

    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        http_client.execute_request(
            method="POST",
            url="http://test.com/raw",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['data'] == "this is raw text"
        assert kwargs['headers']['Content-Type'] == 'text/plain'


def test_execute_request_binary_response(http_client: HTTPExecutor):
    """Test handling of a binary response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'image/png'}
    mock_response.content = b'imagedata'
    mock_response.json.side_effect = ValueError
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        response = http_client.execute_request(
            method="GET",
            url="http://test.com/image.png",
            parameters={},
            request_body=None,
            security_options=None,
            source_name=None
        )

        # Binary content should now be stored as a blob reference
        assert isinstance(response['body'], dict)
        assert 'blob_ref' in response['body']
        assert 'content_type' in response['body']
        assert 'size' in response['body']
        assert response['body']['content_type'] == 'image/png'
        assert response['body']['size'] == 9  # len(b'imagedata')


def test_execute_request_text_response(http_client: HTTPExecutor):
    """Test handling of a text response when JSON fails."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'text/html'}
    mock_response.text = '<html></html>'
    mock_response.json.side_effect = ValueError
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        response = http_client.execute_request(
            method="GET",
            url="http://test.com/page.html",
            parameters={},
            request_body=None,
            security_options=None,
            source_name=None
        )

        assert response['body'] == '<html></html>'


def test_execute_request_content_type_with_none_payload(http_client: HTTPExecutor):
    """Test that a content-type header is sent with a None payload."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.headers = {}
    mock_response.text = ''
    mock_response.json.side_effect = ValueError
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        http_client.execute_request(
            method="POST",
            url="http://test.com/action",
            parameters={},
            request_body={"contentType": "application/json", "payload": None},
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['headers']['Content-Type'] == 'application/json'
        assert kwargs['data'] is None
        assert kwargs['json'] is None

def test_execute_request_no_content_type_infers_json(http_client: HTTPExecutor):
    """Test that a dict payload with no content type is sent as JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.content = b'{"status": "ok"}'
    mock_response.json.return_value = {'status': 'ok'}
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        http_client.execute_request(
            method="POST",
            url="http://test.com/infer",
            parameters={},
            request_body={"contentType": None, "payload": {"key": "value"}},
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['json'] == {"key": "value"}
        assert kwargs['headers']['Content-Type'] == 'application/json'

def test_execute_request_no_content_type_sends_raw_bytes(http_client: HTTPExecutor):
    """Test that a bytes payload with no content type is sent as raw data."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.headers = {}
    mock_response.content = b''
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        http_client.execute_request(
            method="POST",
            url="http://test.com/raw-bytes",
            parameters={},
            request_body={"contentType": None, "payload": b"raw data"},
            security_options=None,
            source_name=None
        )
        
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['data'] == b"raw data"
        assert 'Content-Type' not in kwargs['headers']

def test_execute_request_multipart_with_raw_bytes_fallback(http_client: HTTPExecutor):
    """Test multipart upload where one field is raw bytes."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.content = b'{"status": "ok"}'
    mock_response.json.return_value = {'status': 'ok'}
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        request_body = {
            "contentType": "multipart/form-data",
            "payload": {
                "raw_file": b"raw file content",
                "description": "A test file"
            }
        }
        
        http_client.execute_request(
            method="POST",
            url="http://test.com/upload",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert 'files' in kwargs
        assert kwargs['files']['raw_file'] == ('attachment', b"raw file content", 'application/octet-stream')
        assert kwargs['data']['description'] == 'A test file'


def test_execute_request_network_error(http_client: HTTPExecutor):
    """Test that a network error (e.g., Timeout) is raised."""
    with patch('requests.Session.request', side_effect=requests.exceptions.Timeout("Connection timed out")):
        with pytest.raises(requests.exceptions.Timeout):
            http_client.execute_request(
                method="GET",
                url="http://test.com/timeout",
                parameters={},
                request_body=None,
                security_options=None,
                source_name=None
            )


def test_get_content_type_category(http_client: HTTPExecutor):
    """Test the content type categorization logic with various inputs."""
    test_cases = {
        "application/json": "json",
        "application/hal+json": "json",
        "text/json": "json",
        "multipart/form-data; boundary=123": "multipart",
        "application/x-www-form-urlencoded": "form",
        "text/plain": "raw",
        "image/png": "raw",
        None: "unknown",
        "": "unknown", # Empty string is treated as unknown by implementation
    }
    for content_type, expected_category in test_cases.items():
        category = http_client._get_content_type_category(content_type)
        assert category == expected_category


def test_execute_request_bad_json_response(http_client: HTTPExecutor):
    """Test that a text fallback occurs for an invalid JSON response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/json'} # Mismatched header
    mock_response.text = 'this is not json'
    mock_response.json.side_effect = ValueError("Invalid JSON") # As requests.json() would
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        response = http_client.execute_request(
            method="GET",
            url="http://test.com/bad-json",
            parameters={},
            request_body=None,
            security_options=None,
            source_name=None
        )

        assert response['body'] == 'this is not json'


def test_apply_auth_bearer(http_client: HTTPExecutor):
    """Test applying Bearer token authorization."""
    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="bearer-api",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.HEADER,
                    name="Authorization",
                    auth_value="Bearer my-secret-token"
                )
            )
        ]
    )

    headers, query_params, cookies = {}, {}, {}

    security_options = [
        SecurityOption(requirements=[SecurityRequirement(scheme_name="Authorization", scopes=[])])
    ]

    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    assert headers == {"Authorization": "Bearer my-secret-token"}
    assert query_params == {}
    assert cookies == {}


def test_apply_auth_multiple_options_or_logic(http_client: HTTPExecutor):
    """Test that the second security option is used if the first cannot be satisfied."""
    http_client.auth_provider.get_credentials = Mock(
        return_value=[
            Credential(
                id="x-token",
                request_auth_value=RequestAuthValue(
                    location=AuthLocation.HEADER,
                    name="X-Token",
                    auth_value="my-token"
                )
            )
        ]
    )

    headers, query_params, cookies = {}, {}, {}

    # The real provider would evaluate these as an OR, satisfying the second.
    # The mock provider will find all possible credentials. We assert only one is found.
    security_options = [
        SecurityOption(requirements=[SecurityRequirement(scheme_name="api_key", scopes=[])]),
        SecurityOption(requirements=[SecurityRequirement(scheme_name="X-Token", scopes=[])]),
    ]

    http_client._apply_auth_to_request(
        "https://example.com", headers, query_params, cookies, security_options
    )

    assert headers == {"X-Token": "my-token"}
    assert query_params == {}


def test_execute_request_raw_with_unserializable_payload(http_client: HTTPExecutor):
    """Test sending a non-string/bytes payload with a 'raw' content type."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.headers = {}
    mock_response.content = b''
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        payload = {"this": "is a dict"}
        http_client.execute_request(
            method="POST",
            url="http://test.com/raw-dict",
            parameters={},
            request_body={"contentType": "text/plain", "payload": payload},
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['data'] == str(payload)
        assert kwargs['headers']['Content-Type'] == 'text/plain'

def test_execute_request_multipart_missing_content_key(http_client: HTTPExecutor):
    """Test multipart processing with a file dict missing 'content': should treat it as regular field."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.content = b'{"status": "ok"}'
    mock_response.json.return_value = {"status": "ok"}
    with patch('requests.Session.request', return_value=mock_response) as mock_request:
        request_body = {
            "contentType": "multipart/form-data",
            "payload": {
                "malformed_file": {
                    # Missing 'content' key, should be treated as form field
                    "filename": "test.txt"
                },
                "description": "testing"
            }
        }

        http_client.execute_request(
            method="POST",
            url="http://test.com/upload-bad",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        # No file entries should be present; 'files' may exist but be empty
        assert 'files' in kwargs
        assert kwargs['files'] == {}
        # Data should include the entire dict as a field value
        assert 'data' in kwargs
        assert kwargs['data']['malformed_file'] == {"filename": "test.txt"}
        assert kwargs['data']['description'] == "testing"


def test_execute_request_large_binary_response():
    """Test handling of a larger binary response to ensure it still gets stored as blob."""
    # Create HTTP client with in-memory blob store for testing
    from oak_runner.blob_store import InMemoryBlobStore
    blob_store = InMemoryBlobStore()
    http_client = HTTPExecutor(blob_store=blob_store)
    
    # Create a larger binary payload (e.g., a fake PNG header + data)
    large_binary_data = b'\x89PNG\r\n\x1a\n' + b'x' * 1000  # 1008 bytes
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'image/png'}
    mock_response.content = large_binary_data
    mock_response.json.side_effect = ValueError
    
    with patch('requests.Session.request', return_value=mock_response):
        response = http_client.execute_request(
            method="GET",
            url="http://test.com/large-image.png",
            parameters={},
            request_body=None,
            security_options=None,
            source_name=None
        )

        # Large binary content should also be stored as a blob reference
        assert isinstance(response['body'], dict)
        assert 'blob_ref' in response['body']
        assert 'content_type' in response['body']
        assert 'size' in response['body']
        assert response['body']['content_type'] == 'image/png'
        assert response['body']['size'] == 1008  # len(large_binary_data)
        
        # Verify the actual blob content matches what we expect
        blob_id = response['body']['blob_ref']
        stored_bytes = blob_store.load(blob_id)
        assert stored_bytes == large_binary_data


if __name__ == "__main__":
    pytest.main()
