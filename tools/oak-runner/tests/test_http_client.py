#!/usr/bin/env python3
"""
Tests for the HTTP Client in OAK Runner

This file contains tests for the HTTPExecutor class in the OAK Runner library,
with a focus on authentication handling.
"""

import unittest
import requests
from unittest.mock import patch, MagicMock
from oak_runner.auth.models import SecurityOption, SecurityRequirement, RequestAuthValue, AuthLocation
from oak_runner.http import HTTPExecutor


class MockAuthProvider:
    """Mock authentication provider for testing"""

    def __init__(self, api_configs=None, auth_data=None):
        self.api_configs = api_configs or {}
        self.auth_data = auth_data or {}

    def get_auth_for_api(self, api_id):
        """Return mock auth data for the given API ID"""
        return self.auth_data.get(api_id, {})
        
    def resolve_credentials(self, security_options, source_name: str | None = None):
        """
        Mock implementation of resolve_credentials
        
        Args:
            security_options: List of SecurityOption objects
            source_name: Optional source API name
            
        Returns:
            List of RequestAuthValue objects
        """
        request_auth_values = []
        
        for option in security_options:
            for requirement in option.requirements:
                scheme_name = requirement.scheme_name
                # In the mock, we'll just use the scheme name as the auth key
                # This would be more complex in the real implementation
                for api_id, api_config in self.api_configs.items():
                    # If source_name is provided, only use configs for that source
                    if source_name and api_id != source_name:
                        continue
                        
                    auth_schemes = api_config.get("auth", {}).get("security_schemes", [])
                    
                    for scheme in auth_schemes:
                        if scheme.get("name") == scheme_name:
                            auth_value = self.auth_data.get(api_id, {}).get(scheme_name)
                            if auth_value:
                                location = scheme.get("location", "header")
                                auth_location = None
                                
                                if location == "header":
                                    auth_location = AuthLocation.HEADER
                                elif location == "query":
                                    auth_location = AuthLocation.QUERY
                                elif location == "cookie":
                                    auth_location = AuthLocation.COOKIE
                                else:
                                    auth_location = AuthLocation.HEADER
                                    
                                request_auth_values.append(
                                    RequestAuthValue(
                                        name=scheme_name,
                                        location=auth_location,
                                        auth_value=auth_value
                                    )
                                )
        
        return request_auth_values


class TestHTTPExecutor(unittest.TestCase):
    """Test the HTTP Client functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.http_client = HTTPExecutor()

    def test_init(self):
        """Test that the HTTP client initializes correctly"""
        self.assertIsNotNone(self.http_client)
        self.assertIsNone(self.http_client.auth_provider)

    def test_apply_auth_no_provider(self):
        """Test that auth application is skipped when no auth provider is available"""
        headers = {}
        query_params = {}
        cookies = {}

        # No auth provider set
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies
        )

        # Should not modify any of the dictionaries
        self.assertEqual(headers, {})
        self.assertEqual(query_params, {})
        self.assertEqual(cookies, {})

    def test_apply_auth_query_parameter(self):
        """Test applying auth as query parameters"""
        # Create mock auth provider with query parameter auth
        api_id = "test-api"
        auth_provider = MockAuthProvider(
            api_configs={
                api_id: {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "api-key",
                                "required": True,
                                "location": "query",
                            }
                        ]
                    }
                }
            },
            auth_data={api_id: {"api-key": "test-api-key-12345"}},
        )

        self.http_client.auth_provider = auth_provider

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
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        # Check that query parameters were updated correctly
        self.assertEqual(query_params, {"api-key": "test-api-key-12345"})
        # Headers and cookies should remain empty
        self.assertEqual(headers, {})
        self.assertEqual(cookies, {})

    def test_apply_auth_header(self):
        """Test applying auth as headers"""
        # Create mock auth provider with header auth
        api_id = "test-api"
        auth_provider = MockAuthProvider(
            api_configs={
                api_id: {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "X-Api-Key",
                                "required": True,
                                "location": "header",
                            }
                        ]
                    }
                }
            },
            auth_data={api_id: {"X-Api-Key": "test-api-key-12345"}},
        )

        self.http_client.auth_provider = auth_provider

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
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        # Check that headers were updated correctly
        self.assertEqual(headers, {"X-Api-Key": "test-api-key-12345"})
        # Query params and cookies should remain empty
        self.assertEqual(query_params, {})
        self.assertEqual(cookies, {})

    def test_apply_auth_cookie(self):
        """Test applying auth as cookies"""
        # Create mock auth provider with cookie auth
        api_id = "test-api"
        auth_provider = MockAuthProvider(
            api_configs={
                api_id: {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "session",
                                "required": True,
                                "location": "cookie",
                            }
                        ]
                    }
                }
            },
            auth_data={api_id: {"session": "test-session-id-12345"}},
        )

        self.http_client.auth_provider = auth_provider

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
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        # Check that cookies were updated correctly
        self.assertEqual(cookies, {"session": "test-session-id-12345"})
        # Headers and query params should remain empty
        self.assertEqual(headers, {})
        self.assertEqual(query_params, {})

    def test_apply_auth_multiple_requirements(self):
        """Test applying auth with multiple requirements in different locations"""
        # Create mock auth provider with multiple auth requirements
        api_id = "test-api"
        auth_provider = MockAuthProvider(
            api_configs={
                api_id: {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "api-key",
                                "required": True,
                                "location": "query",
                            },
                            {
                                "type": "apiKey",
                                "name": "X-Client-Id",
                                "required": True,
                                "location": "header",
                            },
                            {
                                "type": "apiKey",
                                "name": "session",
                                "required": True,
                                "location": "cookie",
                            },
                        ]
                    }
                }
            },
            auth_data={
                api_id: {
                    "api-key": "test-api-key-12345",
                    "X-Client-Id": "client-12345",
                    "session": "test-session-id-12345",
                }
            },
        )

        self.http_client.auth_provider = auth_provider

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
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        # Check that all parameters were updated correctly
        self.assertEqual(query_params, {"api-key": "test-api-key-12345"})
        self.assertEqual(headers, {"X-Client-Id": "client-12345"})
        self.assertEqual(cookies, {"session": "test-session-id-12345"})

    def test_apply_auth_missing_value(self):
        """Test handling of missing auth values"""
        # Create mock auth provider with auth requirement but missing value
        api_id = "test-api"
        auth_provider = MockAuthProvider(
            api_configs={
                api_id: {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "api-key",
                                "required": True,
                                "location": "query",
                            }
                        ]
                    }
                }
            },
            auth_data={
                api_id: {
                    # Missing "api-key"
                    "other-key": "value"
                }
            },
        )

        self.http_client.auth_provider = auth_provider

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
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        # All dictionaries should remain empty
        self.assertEqual(headers, {})
        self.assertEqual(query_params, {})
        self.assertEqual(cookies, {})

    def test_apply_auth_unknown_location(self):
        """Test handling of unknown auth location (should default to header)"""
        # Create mock auth provider with unknown auth location
        api_id = "test-api"
        auth_provider = MockAuthProvider(
            api_configs={
                api_id: {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "api-key",
                                "required": True,
                                "location": "unknown",  # Unknown location
                            }
                        ]
                    }
                }
            },
            auth_data={api_id: {"api-key": "test-api-key-12345"}},
        )

        self.http_client.auth_provider = auth_provider

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
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        # Should default to header
        self.assertEqual(headers, {"api-key": "test-api-key-12345"})
        self.assertEqual(query_params, {})
        self.assertEqual(cookies, {})

    def test_apply_auth_multiple_apis(self):
        """Test applying auth from multiple APIs"""
        # Create mock auth provider with multiple APIs
        auth_provider = MockAuthProvider(
            api_configs={
                "api1": {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "api1-key",
                                "required": True,
                                "location": "query",
                            }
                        ]
                    }
                },
                "api2": {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "apiKey",
                                "name": "api2-key",
                                "required": True,
                                "location": "header",
                            }
                        ]
                    }
                },
            },
            auth_data={
                "api1": {"api1-key": "api1-key-value"},
                "api2": {"api2-key": "api2-key-value"},
            },
        )

        self.http_client.auth_provider = auth_provider

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
        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        # Both APIs' auth should be applied
        self.assertEqual(query_params, {"api1-key": "api1-key-value"})
        self.assertEqual(headers, {"api2-key": "api2-key-value"})
        self.assertEqual(cookies, {})

    @patch('requests.Session.request')
    def test_execute_request_multipart(self, mock_request):
        """Test executing a multipart/form-data request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'status': 'ok'}
        mock_request.return_value = mock_response

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
        
        self.http_client.execute_request(
            method="POST",
            url="http://test.com/upload",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['method'], 'POST')
        self.assertEqual(kwargs['url'], 'http://test.com/upload')
        self.assertIn('files', kwargs)
        self.assertEqual(kwargs['files']['file'], ('test.txt', b'file content', 'text/plain'))
        self.assertIn('data', kwargs)
        self.assertEqual(kwargs['data']['description'], 'A test file')
        self.assertNotIn('Content-Type', kwargs['headers']) # requests sets this for multipart

    @patch('requests.Session.request')
    def test_execute_request_json_body(self, mock_request):
        """Test executing a request with a JSON body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'status': 'ok'}
        mock_request.return_value = mock_response

        request_body = {
            "contentType": "application/json",
            "payload": {"key": "value"}
        }

        self.http_client.execute_request(
            method="POST",
            url="http://test.com/data",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )
        
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['json'], {"key": "value"})
        self.assertEqual(kwargs['headers']['Content-Type'], 'application/json')

    @patch('requests.Session.request')
    def test_execute_request_form_body(self, mock_request):
        """Test executing a request with a form URL encoded body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.side_effect = ValueError # no json
        mock_response.text = "Success"
        mock_request.return_value = mock_response

        request_body = {
            "contentType": "application/x-www-form-urlencoded",
            "payload": {"key": "value"}
        }

        self.http_client.execute_request(
            method="POST",
            url="http://test.com/submit",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['data'], {"key": "value"})
        self.assertEqual(kwargs['headers']['Content-Type'], 'application/x-www-form-urlencoded')

    @patch('requests.Session.request')
    def test_execute_request_raw_body(self, mock_request):
        """Test executing a request with a raw string body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.side_effect = ValueError
        mock_response.text = "OK"
        mock_request.return_value = mock_response

        request_body = {
            "contentType": "text/plain",
            "payload": "this is raw text"
        }

        self.http_client.execute_request(
            method="POST",
            url="http://test.com/raw",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['data'], "this is raw text")
        self.assertEqual(kwargs['headers']['Content-Type'], 'text/plain')

    @patch('requests.Session.request')
    def test_execute_request_binary_response(self, mock_request):
        """Test handling of a binary response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.content = b'imagedata'
        mock_response.json.side_effect = ValueError
        mock_request.return_value = mock_response

        response = self.http_client.execute_request(
            method="GET",
            url="http://test.com/image.png",
            parameters={},
            request_body=None,
            security_options=None,
            source_name=None
        )

        self.assertEqual(response['body'], b'imagedata')

    @patch('requests.Session.request')
    def test_execute_request_text_response(self, mock_request):
        """Test handling of a text response when JSON fails."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = '<html></html>'
        mock_response.json.side_effect = ValueError
        mock_request.return_value = mock_response

        response = self.http_client.execute_request(
            method="GET",
            url="http://test.com/page.html",
            parameters={},
            request_body=None,
            security_options=None,
            source_name=None
        )

        self.assertEqual(response['body'], '<html></html>')

    @patch('requests.Session.request')
    def test_execute_request_content_type_with_none_payload(self, mock_request):
        """Test that a content-type header is sent with a None payload."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_response.text = ''
        mock_response.json.side_effect = ValueError
        mock_request.return_value = mock_response

        self.http_client.execute_request(
            method="POST",
            url="http://test.com/action",
            parameters={},
            request_body={"contentType": "application/json", "payload": None},
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['headers']['Content-Type'], 'application/json')
        self.assertIsNone(kwargs['data'])
        self.assertIsNone(kwargs['json'])

    @patch('requests.Session.request')
    def test_execute_request_no_content_type_infers_json(self, mock_request):
        """Test that a dict payload with no content type is sent as JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_request.return_value = mock_response

        self.http_client.execute_request(
            method="POST",
            url="http://test.com/infer",
            parameters={},
            request_body={"contentType": None, "payload": {"key": "value"}},
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['json'], {"key": "value"})
        self.assertEqual(kwargs['headers']['Content-Type'], 'application/json')

    @patch('requests.Session.request')
    def test_execute_request_no_content_type_sends_raw_bytes(self, mock_request):
        """Test that a bytes payload with no content type is sent as raw data."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        self.http_client.execute_request(
            method="POST",
            url="http://test.com/raw-bytes",
            parameters={},
            request_body={"contentType": None, "payload": b"raw data"},
            security_options=None,
            source_name=None
        )
        
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['data'], b"raw data")
        self.assertNotIn('Content-Type', kwargs['headers'])

    @patch('requests.Session.request')
    def test_execute_request_multipart_with_raw_bytes_fallback(self, mock_request):
        """Test multipart upload where one field is raw bytes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_request.return_value = mock_response

        request_body = {
            "contentType": "multipart/form-data",
            "payload": {
                "raw_file": b"raw file content",
                "description": "A test file"
            }
        }
        
        self.http_client.execute_request(
            method="POST",
            url="http://test.com/upload",
            parameters={},
            request_body=request_body,
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertIn('files', kwargs)
        self.assertEqual(kwargs['files']['raw_file'], ('attachment', b"raw file content", 'application/octet-stream'))
        self.assertEqual(kwargs['data']['description'], 'A test file')

    @patch('requests.Session.request')
    def test_execute_request_network_error(self, mock_request):
        """Test that a network error (e.g., Timeout) is raised."""
        mock_request.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaises(requests.exceptions.Timeout):
            self.http_client.execute_request(
                method="GET",
                url="http://test.com/timeout",
                parameters={},
                request_body=None,
                security_options=None,
                source_name=None
            )

    def test_get_content_type_category(self):
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
            with self.subTest(content_type=content_type):
                category = self.http_client._get_content_type_category(content_type)
                self.assertEqual(category, expected_category)

    @patch('requests.Session.request')
    def test_execute_request_bad_json_response(self, mock_request):
        """Test that a text fallback occurs for an invalid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'} # Mismatched header
        mock_response.text = 'this is not json'
        mock_response.json.side_effect = ValueError("Invalid JSON") # As requests.json() would
        mock_request.return_value = mock_response

        response = self.http_client.execute_request(
            method="GET",
            url="http://test.com/bad-json",
            parameters={},
            request_body=None,
            security_options=None,
            source_name=None
        )

        self.assertEqual(response['body'], 'this is not json')

    def test_apply_auth_bearer(self):
        """Test applying Bearer token authorization."""
        api_id = "bearer-api"
        auth_provider = MockAuthProvider(
            api_configs={
                api_id: {
                    "auth": {
                        "security_schemes": [
                            {
                                "type": "http",
                                "scheme": "bearer",
                                "name": "Authorization",
                                "location": "header",
                            }
                        ]
                    }
                }
            },
            auth_data={api_id: {"Authorization": "Bearer my-secret-token"}},
        )
        self.http_client.auth_provider = auth_provider
        headers, query_params, cookies = {}, {}, {}

        security_options = [
            SecurityOption(requirements=[SecurityRequirement(scheme_name="Authorization", scopes=[])])
        ]

        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        self.assertEqual(headers, {"Authorization": "Bearer my-secret-token"})
        self.assertEqual(query_params, {})
        self.assertEqual(cookies, {})

    def test_apply_auth_multiple_options_or_logic(self):
        """Test that the second security option is used if the first cannot be satisfied."""
        auth_provider = MockAuthProvider(
            api_configs={
                "api": {
                    "auth": {
                        "security_schemes": [
                            {"type": "apiKey", "name": "api_key", "location": "query"},
                            {"type": "apiKey", "name": "X-Token", "location": "header"},
                        ]
                    }
                }
            },
            # Only provide auth data for the second scheme
            auth_data={"api": {"X-Token": "my-token"}},
        )
        self.http_client.auth_provider = auth_provider
        headers, query_params, cookies = {}, {}, {}

        # The real provider would evaluate these as an OR, satisfying the second.
        # The mock provider will find all possible credentials. We assert only one is found.
        security_options = [
            SecurityOption(requirements=[SecurityRequirement(scheme_name="api_key", scopes=[])]),
            SecurityOption(requirements=[SecurityRequirement(scheme_name="X-Token", scopes=[])]),
        ]

        self.http_client._apply_auth_to_request(
            "https://example.com", headers, query_params, cookies, security_options
        )

        self.assertEqual(headers, {"X-Token": "my-token"})
        self.assertEqual(query_params, {})

    @patch('requests.Session.request')
    def test_execute_request_raw_with_unserializable_payload(self, mock_request):
        """Test sending a non-string/bytes payload with a 'raw' content type."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        payload = {"this": "is a dict"}
        self.http_client.execute_request(
            method="POST",
            url="http://test.com/raw-dict",
            parameters={},
            request_body={"contentType": "text/plain", "payload": payload},
            security_options=None,
            source_name=None
        )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['data'], str(payload))
        self.assertEqual(kwargs['headers']['Content-Type'], 'text/plain')

    @patch('requests.Session.request')
    def test_execute_request_multipart_missing_content_key(self, mock_request):
        """Test multipart processing with a file dict missing 'content': should treat it as regular field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response

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

        self.http_client.execute_request(
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
        self.assertIn('files', kwargs)
        self.assertEqual(kwargs['files'], {})
        # Data should include the entire dict as a field value
        self.assertIn('data', kwargs)
        self.assertEqual(kwargs['data']['malformed_file'], {"filename": "test.txt"})
        self.assertEqual(kwargs['data']['description'], "testing")


if __name__ == "__main__":
    unittest.main()
