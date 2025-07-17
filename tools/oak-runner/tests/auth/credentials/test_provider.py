import base64
from unittest.mock import MagicMock

import pytest

from oak_runner.auth.credentials.fetch import FetchOptions
from oak_runner.auth.credentials.provider import CredentialProviderFactory
from oak_runner.auth.credentials.models import Credential
from oak_runner.auth.models import (
    AuthLocation,
    SecurityOption,
    SecurityRequirement,
    RequestAuthValue,
    EnvVarKeys,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_key_req():
    return {
        "type": "apiKey",
        "name": "ApiKey",
        "location": "header",
        "security_scheme_name": "ApiKeyAuth",
    }


@pytest.fixture
def bearer_req():
    return {
        "type": "http",
        "schemes": ["bearer"],
        "name": "Authorization",
        "location": "header",
        "security_scheme_name": "BearerAuth",
    }


@pytest.fixture
def basic_req():
    return {
        "type": "http",
        "schemes": ["basic"],
        "name": "Authorization",
        "location": "header",
        "security_scheme_name": "BasicAuth",
    }


@pytest.fixture
def env_mappings():
    return {
        "ApiKeyAuth": {EnvVarKeys.API_KEY: "TEST_API_KEY"},
        "BearerAuth": {EnvVarKeys.TOKEN: "TEST_BEARER_TOKEN"},
        "BasicAuth": {
            EnvVarKeys.USERNAME: "TEST_USERNAME",
            EnvVarKeys.PASSWORD: "TEST_PASSWORD",
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_resolve_credentials_api_key(api_key_req, env_mappings, monkeypatch):
    """Test resolving API Key credentials."""
    monkeypatch.setenv("TEST_API_KEY", "test-api-key-value")
    monkeypatch.setenv("TEST_BEARER_TOKEN", "test-bearer-token-value")
    monkeypatch.setenv("TEST_USERNAME", "test-username")
    monkeypatch.setenv("TEST_PASSWORD", "test-password")
    
    # Create provider with API Key auth requirement
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[api_key_req]
    )
    
    # Create security option with API Key requirement
    security_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="ApiKeyAuth", scopes=[])
        ]
    )
    
    # Resolve credentials
    result = provider.get_credentials([security_option])
    
    # Verify result
    assert len(result) == 1
    assert isinstance(result[0], Credential)
    assert result[0].request_auth_value.location == AuthLocation.HEADER
    assert result[0].request_auth_value.name == "ApiKey"
    assert result[0].request_auth_value.auth_value == "test-api-key-value"



def test_resolve_credentials_bearer(env_mappings, bearer_req, monkeypatch):
    """Test resolving Bearer token credentials."""
    monkeypatch.setenv("TEST_BEARER_TOKEN", "test-bearer-token-value")
    monkeypatch.setenv("TEST_USERNAME", "test-username")
    monkeypatch.setenv("TEST_PASSWORD", "test-password")
    monkeypatch.setenv("TEST_API_KEY", "test-api-key-value")
    
    # Create provider with Bearer auth requirement
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[bearer_req]
    )
    
    # Create security option with Bearer requirement
    security_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="BearerAuth", scopes=[])
        ]
    )
    
    # Resolve credentials
    result = provider.get_credentials([security_option])
    
    # Verify result
    assert len(result) == 1
    assert isinstance(result[0], Credential)
    assert result[0].request_auth_value.location == AuthLocation.HEADER
    assert result[0].request_auth_value.name == "Authorization"
    assert result[0].request_auth_value.auth_value == "Bearer test-bearer-token-value"


def test_resolve_credentials_basic(env_mappings, basic_req, monkeypatch):
    """Test resolving Basic auth credentials."""
    monkeypatch.setenv("TEST_USERNAME", "test-username")
    monkeypatch.setenv("TEST_PASSWORD", "test-password")
    monkeypatch.setenv("TEST_API_KEY", "test-api-key-value")
    monkeypatch.setenv("TEST_BEARER_TOKEN", "test-bearer-token-value")
    
    # Create provider with Basic auth requirement
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[basic_req]
    )
    
    # Create security option with Basic auth requirement
    security_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="BasicAuth", scopes=[])
        ]
    )
    
    # Resolve credentials
    result = provider.get_credentials([security_option])
    
    # Verify result
    assert len(result) == 1
    assert isinstance(result[0], Credential)
    assert result[0].request_auth_value.location == AuthLocation.HEADER
    assert result[0].request_auth_value.name == "Authorization"
    
    # Basic auth value should be base64 encoded username:password
    expected_value = f"Basic {base64.b64encode(b'test-username:test-password').decode()}"
    assert result[0].request_auth_value.auth_value == expected_value


def test_resolve_credentials_missing_env_vars(env_mappings, monkeypatch, basic_req):
    """Test resolving credentials with missing environment variables."""
    monkeypatch.setenv("TEST_API_KEY", "test-api-key-value")
    monkeypatch.setenv("TEST_BEARER_TOKEN", "test-bearer-token-value")
    
    # Create provider with Basic auth requirement (but missing env vars)
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[basic_req]
    )
    
    # Create security option with Basic auth requirement
    security_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="BasicAuth", scopes=[])
        ]
    )
    
    # Resolve credentials - should return empty list since env vars are missing
    result = provider.get_credentials([security_option])
    
    # Verify result is empty
    assert len(result) == 0


def test_resolve_credentials_multiple_options(env_mappings, api_key_req, bearer_req, basic_req, monkeypatch):
    """Test resolving credentials with multiple security options."""
    monkeypatch.setenv("TEST_API_KEY", "test-api-key-value")
    monkeypatch.setenv("TEST_BEARER_TOKEN", "test-bearer-token-value")
    monkeypatch.setenv("TEST_USERNAME", "test-username")
    monkeypatch.setenv("TEST_PASSWORD", "test-password")
        
    # Create provider with multiple auth requirements
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[api_key_req, bearer_req, basic_req]
    )
    
    # Create security options (API Key OR Bearer)
    api_key_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="ApiKeyAuth", scopes=[])
        ]
    )
    bearer_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="BearerAuth", scopes=[])
        ]
    )
    
    # Resolve credentials with multiple options
    result = provider.get_credentials([api_key_option, bearer_option])
    
    # Verify result - should process all options that resolve successfully
    assert len(result) == 2
    
    # First result should be from the first option (API Key)
    assert isinstance(result[0], Credential)
    assert result[0].request_auth_value.location == AuthLocation.HEADER
    assert result[0].request_auth_value.name == "ApiKey"
    assert result[0].request_auth_value.auth_value == "test-api-key-value"
    
    # Second result should be from the second option (Bearer)
    assert isinstance(result[1], Credential)
    assert result[1].request_auth_value.location == AuthLocation.HEADER
    assert result[1].request_auth_value.name == "Authorization"
    assert result[1].request_auth_value.auth_value == "Bearer test-bearer-token-value"


def test_resolve_credentials_combined_requirements(env_mappings, api_key_req, bearer_req, monkeypatch):
    """Test resolving credentials with combined security requirements (AND relationship)."""
    monkeypatch.setenv("TEST_API_KEY", "test-api-key-value")
    monkeypatch.setenv("TEST_BEARER_TOKEN", "test-bearer-token-value")
    
    # Create provider with multiple auth requirements
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[api_key_req, bearer_req]
    )
    
    # Create security option with multiple requirements (API Key AND Bearer)
    combined_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="ApiKeyAuth", scopes=[]),
            SecurityRequirement(scheme_name="BearerAuth", scopes=[])
        ]
    )
    
    # Resolve credentials
    result = provider.get_credentials([combined_option])
    
    # Verify result - should return both auth values
    assert len(result) == 2
    
    # First result should be API Key
    assert isinstance(result[0], Credential)
    assert result[0].request_auth_value.location == AuthLocation.HEADER
    assert result[0].request_auth_value.name == "ApiKey"
    assert result[0].request_auth_value.auth_value == "test-api-key-value"
    
    # Second result should be Bearer token
    assert isinstance(result[1], Credential)
    assert result[1].request_auth_value.location == AuthLocation.HEADER
    assert result[1].request_auth_value.name == "Authorization"
    assert result[1].request_auth_value.auth_value == "Bearer test-bearer-token-value"


def test_resolve_credentials_with_source_name(env_mappings, monkeypatch):
    """Test resolving credentials with source_name parameter."""
    monkeypatch.setenv("TEST_API_KEY_SOURCE1", "api-key-from-source1")
    monkeypatch.setenv("TEST_API_KEY_SOURCE2", "api-key-from-source2")
    monkeypatch.setenv("TEST_BEARER_TOKEN_SOURCE1", "bearer-token-from-source1")
    monkeypatch.setenv("TEST_BEARER_TOKEN_SOURCE2", "bearer-token-from-source2")
    
    # Create auth requirements with the same scheme name but different source descriptions
    api_key_req_source1 = {
        "type": "apiKey",
        "name": "ApiKey",
        "location": "header",
        "security_scheme_name": "ApiKeyAuth",
        "source_description_id": "source1"
    }
    
    api_key_req_source2 = {
        "type": "apiKey",
        "name": "ApiKey",
        "location": "header",
        "security_scheme_name": "ApiKeyAuth",
        "source_description_id": "source2"
    }
    
    # Create environment mappings with source name as the outer key
    env_mappings = {
        "source1": {
            "ApiKeyAuth": {
                EnvVarKeys.API_KEY: "TEST_API_KEY_SOURCE1"
            }
        },
        "source2": {
            "ApiKeyAuth": {
                EnvVarKeys.API_KEY: "TEST_API_KEY_SOURCE2"
            }
        }
    }
    
    # Create provider with auth requirements from both sources
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[api_key_req_source1, api_key_req_source2]
    )
    
    # Create security option with ApiKeyAuth requirement
    security_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="ApiKeyAuth", scopes=[])
        ]
    )
    fetch_options = FetchOptions(source_name="source1")
    # Test 1: Resolve with source1
    result_source1 = provider.get_credentials([security_option], fetch_options)
    
    # Verify result for source1
    assert len(result_source1) == 1
    assert isinstance(result_source1[0], Credential)
    assert result_source1[0].request_auth_value.location == AuthLocation.HEADER
    assert result_source1[0].request_auth_value.name == "ApiKey"
    assert result_source1[0].request_auth_value.auth_value == "api-key-from-source1"
    
    # Test 2: Resolve with source2
    fetch_options = FetchOptions(source_name="source2")
    result_source2 = provider.get_credentials([security_option], fetch_options)
    
    # Verify result for source2
    assert len(result_source2) == 1
    assert isinstance(result_source2[0], Credential)
    assert result_source2[0].request_auth_value.location == AuthLocation.HEADER
    assert result_source2[0].request_auth_value.name == "ApiKey"
    assert result_source2[0].request_auth_value.auth_value == "api-key-from-source2"

    # Ensure deprecate method still works
    result_source1_deprecated = provider.resolve_credentials([security_option], "source1")
    assert len(result_source1_deprecated) == 1
    assert isinstance(result_source1_deprecated[0], RequestAuthValue)
    assert result_source1_deprecated[0].location == AuthLocation.HEADER
    assert result_source1_deprecated[0].name == "ApiKey"
    assert result_source1_deprecated[0].auth_value == "api-key-from-source1"

    result_source2_deprecated = provider.resolve_credentials([security_option], "source2")
    assert len(result_source2_deprecated) == 1
    assert isinstance(result_source2_deprecated[0], RequestAuthValue)
    assert result_source2_deprecated[0].location == AuthLocation.HEADER
    assert result_source2_deprecated[0].name == "ApiKey"
    assert result_source2_deprecated[0].auth_value == "api-key-from-source2"


def test_resolve_credentials_with_conflicting_scheme_names(monkeypatch):
    """Test resolving credentials with conflicting scheme names from different sources."""
    monkeypatch.setenv("TEST_API_KEY_SOURCE1", "api-key-from-source1")
    monkeypatch.setenv("TEST_API_KEY_SOURCE2", "api-key-from-source2")
    # Create auth requirements with the same scheme name but different source descriptions
    api_key_req_source1 = {
        "type": "apiKey",
        "name": "ApiKey-Source1",  # Different name to distinguish in results
        "location": "header",
        "security_scheme_name": "ApiKeyAuth",  # Same scheme name
        "source_description_id": "source1"
    }
    
    api_key_req_source2 = {
        "type": "apiKey",
        "name": "ApiKey-Source2",  # Different name to distinguish in results
        "location": "header",
        "security_scheme_name": "ApiKeyAuth",  # Same scheme name
        "source_description_id": "source2"
    }
    
    # Create environment mappings with source name as the outer key
    env_mappings = {
        "source1": {
            "ApiKeyAuth": {
                EnvVarKeys.API_KEY: "TEST_API_KEY_SOURCE1"
            }
        },
        "source2": {
            "ApiKeyAuth": {
                EnvVarKeys.API_KEY: "TEST_API_KEY_SOURCE2"
            }
        }
    }
    
    # Create provider with auth requirements from both sources
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=MagicMock(),
        auth_requirements=[api_key_req_source1, api_key_req_source2]
    )
    
    # Create security option with ApiKeyAuth requirement
    security_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="ApiKeyAuth", scopes=[])
        ]
    )
    
    # Test 1: Resolve with source1
    fetch_options = FetchOptions(source_name="source1")
    result_source1 = provider.get_credentials([security_option], fetch_options)
    
    # Verify result for source1
    assert len(result_source1) == 1
    assert result_source1[0].request_auth_value.name == "ApiKey-Source1"
    assert result_source1[0].request_auth_value.auth_value == "api-key-from-source1"
    
    # Test 2: Resolve with source2
    fetch_options = FetchOptions(source_name="source2")
    result_source2 = provider.get_credentials([security_option], fetch_options)
    
    # Verify result for source2
    assert len(result_source2) == 1
    assert result_source2[0].request_auth_value.name == "ApiKey-Source2"
    assert result_source2[0].request_auth_value.auth_value == "api-key-from-source2"
    
    # Test 3: Resolve with source1 (instead of relying on the code to find any source)
    fetch_options = FetchOptions(source_name="source1")
    result_no_source = provider.get_credentials([security_option], fetch_options)
    
    # Verify result - we expect the source1 scheme since we specified it
    assert len(result_no_source) == 1
    assert result_no_source[0].request_auth_value.name == "ApiKey-Source1"
    assert result_no_source[0].request_auth_value.auth_value == "api-key-from-source1"


def test_resolve_credentials_oauth2_client_credentials(monkeypatch, env_mappings):
    """Test resolving OAuth2 credentials using client credentials flow."""
    monkeypatch.setenv("TEST_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("TEST_CLIENT_SECRET", "test-client-secret")
        
    # Create OAuth2 auth requirement with client credentials flow
    oauth2_req = {
        "type": "oauth2",
        "flow_type": "clientCredentials",
        "scopes": ["read", "write"],
        "security_scheme_name": "OAuth2Auth",
        "auth_urls": {
            "token": "https://example.com/token"
        }
    }
    
    # Create environment mappings for OAuth2 client credentials
    env_mappings = {
        "OAuth2Auth.clientCredentials": {
            EnvVarKeys.CLIENT_ID: "TEST_CLIENT_ID",
            EnvVarKeys.CLIENT_SECRET: "TEST_CLIENT_SECRET"
        }
    }
    
    # Create mock HTTP client
    mock_http_client = MagicMock()
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "dynamic-access-token",
        "token_type": "bearer",
        "expires_in": 3600
    }
    
    # Set up HTTP client to return mock response
    mock_http_client.post.return_value = mock_response
    
    # Create provider with OAuth2 auth requirement and mock HTTP client
    provider = CredentialProviderFactory.create_default(
        env_mapping=env_mappings,
        http_client=mock_http_client,
        auth_requirements=[oauth2_req]
    )
    
    # Create security option with OAuth2 requirement
    security_option = SecurityOption(
        requirements=[
            SecurityRequirement(scheme_name="OAuth2Auth", scopes=["read", "write"])
        ]
    )
    
    # Resolve credentials
    result = provider.get_credentials([security_option])
    
    # Verify HTTP request was made with correct parameters
    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    
    # Check data
    assert call_args[1]['data'] == {
        "grant_type": "client_credentials",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "scope": "read write"
    }
    
    # Verify result
    assert len(result) == 1
    assert isinstance(result[0], Credential)
    assert result[0].request_auth_value.location == AuthLocation.HEADER
    assert result[0].request_auth_value.name == "Authorization"
    assert result[0].request_auth_value.auth_value == "Bearer dynamic-access-token"
