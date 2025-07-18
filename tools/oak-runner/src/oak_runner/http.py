#!/usr/bin/env python3
"""
HTTP Client for OAK Runner

This module provides HTTP request handling for the OAK Runner.
"""
import logging
import os
from typing import Any
from typing import Optional
from oak_runner.auth.models import SecurityOption, RequestAuthValue, AuthLocation
from oak_runner.auth.credentials.provider import CredentialProvider
from oak_runner.auth.credentials.fetch import FetchOptions
from oak_runner.auth.credentials.models import Credential
import requests
from oak_runner.blob_utils import analyze_response_for_blob

# Configure logging
logger = logging.getLogger("arazzo-runner.http")


class HTTPExecutor:
    """HTTP client for executing API requests in Arazzo workflows"""

    def __init__(self, http_client=None, auth_provider: Optional[CredentialProvider] = None):
        """
        Initialize the HTTP client

        Args:
            http_client: Optional HTTP client (defaults to requests.Session)
            auth_provider: Optional authentication provider
        """
        self.http_client = http_client or requests.Session()
        self.auth_provider: Optional[CredentialProvider] = auth_provider

    def _get_content_type_category(self, content_type: str | None) -> str:
        """
        Categorize the content type to determine how to handle the request body.
        
        Args:
            content_type: The content type string from the request body
            
        Returns:
            One of: 'multipart', 'json', 'form', 'raw', or 'unknown'
        """
        if not content_type:
            return 'unknown'
            
        content_type_lower = content_type.lower()
        
        if "multipart/form-data" in content_type_lower:
            return 'multipart'
        elif "json" in content_type_lower:
            return 'json'
        elif "form" in content_type_lower or "x-www-form-urlencoded" in content_type_lower:
            return 'form'
        else:
            return 'raw'

    def _is_binary_content(self, content_type: str) -> bool:
        """
        Check if content type represents binary data.
        
        Args:
            content_type: The Content-Type header value
            
        Returns:
            True if content is binary, False otherwise
        """
        if not content_type:
            return False
            
        content_type_lower = content_type.lower()
        binary_prefixes = [
            "application/octet-stream",
            "audio/",
            "video/",
            "image/",
            "application/pdf",
            "application/zip",
            "application/x-tar",
            "application/gzip"
        ]
        
        return any(content_type_lower.startswith(prefix) for prefix in binary_prefixes)

    def _get_response_content(self, response) -> Any:
        """
        Get appropriate response content based on content type.
        Returns the actual data without any blob storage logic.
        
        Processing order: JSON -> Binary -> Text

        Args:
            response: The HTTP response object

        Returns:
            The response content in appropriate format (JSON, text, or bytes)
        """
        content_type = response.headers.get("Content-Type", "")
        
        # 1. Try JSON first for JSON content types
        if "json" in content_type.lower():
            try:
                return response.json()
            except Exception:
                logger.debug("Failed to parse JSON despite JSON content-type, falling back")
        
        # 2. For binary content types, return raw bytes
        if self._is_binary_content(content_type):
            return response.content
        
        # 3. Default to text for everything else
        return response.text

    def execute_request(
        self, method: str, url: str, parameters: dict[str, Any], request_body: dict | None, security_options: list[SecurityOption] | None = None, source_name: str | None = None
    ) -> dict:
        """
        Execute an HTTP request using the configured client

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: URL to request
            parameters: Dictionary of parameters by location (path, query, header, cookie)
            request_body: Optional request body
            security_options: Optional list of security options for authentication
            source_name: Source API name to distinguish between APIs with conflicting scheme names

        Returns:
            response: Dictionary with status_code, headers, body
        """
        # Replace path parameters in the URL
        path_params = parameters.get("path", {})
        for name, value in path_params.items():
            url = url.replace(f"{{{name}}}", str(value))

        # Prepare query parameters
        query_params = parameters.get("query", {})

        # Prepare headers
        headers = parameters.get("header", {})

        # Prepare cookies
        cookies = parameters.get("cookie", {})

        # Log security options
        if security_options:
            logger.debug(f"Security options: {security_options}")
            for i, option in enumerate(security_options):
                logger.debug(f"Option {i} requirements: {option}")

        # Apply authentication headers from auth_provider if available
        self._apply_auth_to_request(url, headers, query_params, cookies, security_options, source_name)

        # Prepare request body
        data = None
        json_data = None
        files = None

        if request_body:
            content_type = request_body.get("contentType")
            payload = request_body.get("payload")
            content_category = self._get_content_type_category(content_type)

            # Handle explicit None payload
            if payload is None:
                if content_type:
                    # Content type specified but no payload - set header but no body
                    headers["Content-Type"] = content_type
                    logger.debug(f"Content type '{content_type}' specified but payload is None - sending empty body with header")
                # If no content_type either, just send empty body (no header needed)

            elif content_category == 'multipart':
                # Path 1: Multipart form data with file uploads
                files = {}
                data = {}
                for key, value in payload.items():
                    # A field is treated as a file upload if its value is an object
                    # containing 'content' and 'filename' keys.
                    if isinstance(value, dict) and "content" in value and "filename" in value:
                        # requests expects a tuple: (filename, file_data, content_type)
                        file_content = value["content"]
                        file_name = value["filename"] if value.get("filename") else "attachment"
                        file_type = value.get("contentType", "application/octet-stream")
                        files[key] = (file_name, file_content, file_type)
                        logger.debug(f"Preparing file '{file_name}' for upload.")
                    elif isinstance(value, (bytes, bytearray)):
                        # Fallback: treat raw bytes as a file with a generic name
                        files[key] = ("attachment", value, "application/octet-stream")
                        logger.debug(f"Preparing raw-bytes payload as file for key '{key}'.")
                    else:
                        data[key] = value
                # Do NOT set Content-Type header here; `requests` will do it with the correct boundary

            elif content_category == 'json':
                # Path 2: JSON content
                headers["Content-Type"] = content_type
                json_data = payload

            elif content_category == 'form':
                # Path 3: Form-encoded content
                headers["Content-Type"] = content_type
                if isinstance(payload, dict):
                    data = payload
                else:
                    logger.warning(f"Form content type specified, but payload is not a dictionary: {type(payload)}. Sending as raw data.")
                    data = payload

            elif content_category == 'raw':
                # Path 4: Other explicit content types (raw data)
                headers["Content-Type"] = content_type
                if isinstance(payload, (str, bytes)):
                    data = payload
                else:
                    # Attempt to serialize other types? Or raise error? Let's log and convert to string for now.
                    logger.warning(f"Payload type {type(payload)} not directly supported for raw data. Converting to string.")
                    data = str(payload)

            elif content_category == 'unknown' and payload is not None:
                # Path 5: No content type specified but payload exists - try to infer
                if isinstance(payload, dict):
                    headers["Content-Type"] = "application/json"
                    json_data = payload
                    logger.debug("No content type specified, inferring application/json for dict payload")
                elif isinstance(payload, (bytes, bytearray)):
                    data = payload
                    logger.debug("No content type specified, sending raw bytes")
                elif isinstance(payload, str):
                    data = payload
                    logger.debug("No content type specified, sending raw string")
                else:
                    logger.warning(f"Payload provided but contentType is missing and type {type(payload)} cannot be inferred; body not sent.")

        # Log request details for debugging
        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Request headers: {headers}")
        if query_params:
            logger.debug(f"Query parameters: {query_params}")
        if cookies:
            logger.debug(f"Cookies: {cookies}")

        # Execute the request
        response = self.http_client.request(
            method=method,
            url=url,
            params=query_params,
            headers=headers,
            cookies=cookies,
            data=data,
            json=json_data,
            files=files,
        )

        # Get the response content in appropriate format
        body_value = self._get_response_content(response)
        
        # Analyze blob storage metadata without actually storing
        is_binary = self._is_binary_content(response.headers.get("Content-Type", ""))
        blob_metadata = analyze_response_for_blob(response, is_binary)

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body_value,
            "blob_metadata": blob_metadata,
        }

    def _apply_auth_to_request(
        self,
        url: str,
        headers: dict[str, str],
        query_params: dict[str, str],
        cookies: dict[str, str],
        security_options: list[SecurityOption] | None = None,
        source_name: str | None = None,
    ) -> None:
        """
        Apply authentication values from auth_provider to the request

        Args:
            url: The request URL
            headers: Headers dictionary to modify
            query_params: Query parameters dictionary to modify
            cookies: Cookies dictionary to modify
            security_options: List of security options to use for authentication
        """
        if not self.auth_provider:
            logger.debug("No auth_provider available, skipping auth application")
            return

        try:
            # If security options are provided, use them to resolve credentials
            if security_options:
                logger.debug(f"Resolving credentials for security options: {security_options}")
                
                # Get auth values for the security requirements
                fetch_options = FetchOptions(
                    source_name=source_name
                )
                credentials: list[Credential] = self.auth_provider.get_credentials(security_options, fetch_options)
                if not credentials:
                    logger.debug("No credentials resolved for the security requirements")
                    return

                # Apply each auth value to the request
                for credential in credentials:
                    auth_value: RequestAuthValue = credential.request_auth_value
                    if auth_value.location == AuthLocation.QUERY:
                        query_params[auth_value.name] = auth_value.auth_value
                        logger.debug(f"Applied '{auth_value.name}' as query parameter")
                    elif auth_value.location == AuthLocation.HEADER:
                        headers[auth_value.name] = auth_value.auth_value
                        logger.debug(f"Applied '{auth_value.name}' as header")
                    elif auth_value.location == AuthLocation.COOKIE:
                        cookies[auth_value.name] = auth_value.auth_value
                        logger.debug(f"Applied '{auth_value.name}' as cookie")
                    else:
                        # Default to header for unknown locations
                        headers[auth_value.name] = auth_value.auth_value
                        logger.debug(f"Applied '{auth_value.name}' as header (default)")

            # Also check for direct auth values in auth_provider
            if hasattr(self.auth_provider, "get_auth_value"):
                for header_name in ["Authorization", "Api-Key", "X-Api-Key", "Token"]:
                    if header_name not in headers:
                        auth_value = self.auth_provider.get_auth_value(header_name)
                        if auth_value:
                            headers[header_name] = auth_value
                            logger.debug(f"Applied {header_name} from auth_provider")
        except Exception as e:
            logger.error(f"Error applying auth to request: {e}")
            # Don't re-raise, just log and continue
