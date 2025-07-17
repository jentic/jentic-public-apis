from abc import ABC, abstractmethod
import base64
import logging

from oak_runner.auth.credentials.models import Credential
from oak_runner.auth.auth_parser import (
    AuthType, 
    AuthLocation,
)
from oak_runner.auth.models import (
    RequestAuthValue, 
    AuthLocation,
    BasicAuth, 
    BearerAuth, 
    RequestAuthValue,
)

logger = logging.getLogger(__name__)

class CredentialTransformer(ABC):
    """Abstract base class for credential transformers."""
    
    @abstractmethod
    def transform(self, credential: Credential) -> Credential:
        """Transform a credential."""
        raise NotImplementedError


class CredentialToRequestAuthValueTransformer(CredentialTransformer):
    """Transform Credential and create RequestAuthValue."""
    
    def transform(self, credential: Credential) -> Credential:
        match credential.auth_value.type:
            case AuthType.API_KEY:
                credential.request_auth_value = RequestAuthValue(
                    location=credential.security_scheme.location,
                    name=credential.security_scheme.name,
                    auth_value=credential.auth_value.api_key
                )
            case AuthType.HTTP:  # Handle HTTP auth types
                if isinstance(credential.auth_value, BearerAuth):
                    credential.request_auth_value = RequestAuthValue(
                        location=credential.security_scheme.location,
                        name="Authorization",
                        auth_value=f"Bearer {credential.auth_value.token}"
                    )
                elif isinstance(credential.auth_value, BasicAuth):
                    # Basic auth requires base64 encoding of username:password
                    auth_string = f"{credential.auth_value.username}:{credential.auth_value.password}"
                    encoded = base64.b64encode(auth_string.encode()).decode()
                    credential.request_auth_value = RequestAuthValue(
                        location=credential.security_scheme.location,
                        name="Authorization",
                        auth_value=f"Basic {encoded}"
                    )

            case AuthType.OAUTH2 | AuthType.OPENID:
                credential.request_auth_value = RequestAuthValue(
                    location=AuthLocation.HEADER,
                    name="Authorization",
                    auth_value=f"Bearer {credential.auth_value.access_token}"
                )
            case AuthType.CUSTOM:
                if hasattr(credential.auth_value, 'api_key'):
                    credential.request_auth_value = RequestAuthValue(
                        location=credential.security_scheme.location,
                        name=credential.security_scheme.name,
                        auth_value=credential.auth_value.api_key
                    )
            case _:
                logger.warning(f"No conversion available for auth type: {credential.auth_value.type}")

        return credential
