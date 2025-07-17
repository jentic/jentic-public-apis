# Strategy pattern for credential fetching
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
import os
import requests
from typing import Dict, List

from oak_runner.auth.credentials.models import Credential
from oak_runner.auth.auth_parser import (
    AuthType, 
    AuthLocation,
    AuthRequirement,
    HttpSchemeType
)
from oak_runner.auth.models import (
    ApiKeyAuth, 
    BasicAuth, 
    BearerAuth, 
    EnvVarKeys,
    OAuth2AccessTokenOnly,
    SecurityOption,
    SecurityScheme,
    AuthValue,
    ApiKeyScheme,
    HttpAuthScheme,
    OAuth2Scheme,
    OpenIDScheme,
    CustomScheme,
    OAuth2Urls,
    OAuth2Flows,
    OAuth2FlowType,
    ImplicitFlow,
    AuthorizationCodeFlow,
    ClientCredentialsFlow,
    PasswordFlow
)

logger = logging.getLogger(__name__)


@dataclass
class FetchOptions:
    """Optional parameters that tweak how credentials are looked-up or resolved
    by a `FetchStrategy`.

    Parameters
    ----------
    source_name: str | None, default ``None``
        Identifier of the *source description* (for example the filename of an
        external OpenAPI document or an API server name) whose security scheme
        definitions should be consulted.  When ``None`` each strategy falls
        back to its own default (commonly ``"default"`` or the first available
        source).
    """
    source_name: str | None = None


class FetchStrategy(ABC):
    """Defines the synchronous interface that all credential-fetch mechanisms
    must implement.

    A concrete `FetchStrategy` is responsible for turning *security options*—the
    set of `SecurityOption` objects required for a request—into concrete
    `Credential` instances.

    Lifecycle
    ~~~~~~~~~
    1. ``fetch`` / ``fetch_one`` are invoked at runtime to retrieve the actual
    credentials needed for outgoing requests. These may involve network calls,
    secret-store look-ups, environment variable reads, etc.

    Methods
    -------
    fetch(requests, options)
        Retrieve credentials for a batch of ``SecurityOption`` instances.
    fetch_one(request, options)
        Retrieve credentials for a single ``SecurityOption`` instance.
    """
    
    @abstractmethod
    def fetch(self, requests: List[SecurityOption], options: FetchOptions | None = None) -> List[Credential]:
        """Fetch credential(s) based on requests."""
        raise NotImplementedError
    
    @abstractmethod
    def fetch_one(self, request: SecurityOption, options: FetchOptions | None = None) -> List[Credential]:
        """Fetch credential(s) based on request."""
        raise NotImplementedError


class EnvironmentVariableFetchStrategy(FetchStrategy):
    """Fetch credentials from environment variables."""
    
    def __init__(
        self,
        env_mapping: Dict[str, str] | None = None,
        http_client: requests.Session | None = None,
        auth_requirements: List[AuthRequirement] = None
    ):
        self._env_mapping: Dict[str, str] = env_mapping or {}
        self._http_client: requests.Session | None = http_client
        self._auth_requirements: List[AuthRequirement] = auth_requirements or []
        self._security_schemes: Dict[str, Dict[str, SecurityScheme]] = \
            create_security_schemes_from_auth_requirements(self._auth_requirements)

    def fetch_one(self, request: SecurityOption, options: FetchOptions | None = None) -> List[Credential]:
        """
        Fetch credential from environment variable.
        """
        logger.debug(f"Fetching credential for {request=}")
        credentials = []
        source_name = options.source_name if options else "default"
        
        for requirement in request.requirements:
            scheme_name = requirement.scheme_name
            logger.debug(f'Resolving auth scheme: {scheme_name} from source: {source_name}')
            
            # Try to find the scheme using source description if available
            scheme = self._get_security_scheme(scheme_name, source_name)
            if not scheme:
                continue
            
            logger.debug(f'Found matching auth scheme: {scheme_name}')
            credentials.append(
                Credential(
                    id=f"env-{scheme_name}",
                    security_scheme=scheme,
                    auth_value=self._resolve_auth_value(scheme_name, source_name, requirement.scopes)
                )
            )

        return credentials

    def fetch(self, requests: List[SecurityOption], options: FetchOptions | None = None) -> List[Credential]:
        """Fetch credential from environment variable."""
        # Fetch credentials for each request one at a time, as its going to the env
        # we dont need to batch this (but we could)
        credentials = []
        for req in requests:
            credentials.extend(self.fetch_one(req, options))
        return credentials

    ###########################################################################
    ###################### Private API ########################################
    ###########################################################################
    def _resolve_auth_value(
        self, 
        scheme_name: str, 
        source_name: str | None = None, 
        scopes: List[str] | None = None
    ) -> AuthValue | None:
        """
        Resolve authentication value for a security scheme.
        
        Args:
            scheme: The security scheme
            source_name: Source name of the security scheme
            scopes: Optional list of scopes required for this authentication
            
        Returns:
            AuthValue if resolved, None otherwise
        """
        scheme = self._get_security_scheme(scheme_name, source_name)
        
        if not scheme:
            return None
            
        logger.debug(f"Resolving auth value for {scheme=}, {source_name=}, {scopes=}")
        if scheme.type == AuthType.API_KEY:
            logger.debug(f"Resolving API key for {scheme_name=}")
            api_key = self._loadFromEnvironment(scheme_name, EnvVarKeys.API_KEY, source_name)
            if not api_key:
                return None

            return ApiKeyAuth(
                type=AuthType.API_KEY,
                api_key=api_key
            )
        elif scheme.type == AuthType.HTTP:
            scheme: HttpAuthScheme = scheme
            # Handle HTTP auth types based on scheme
            if scheme.scheme == HttpSchemeType.BEARER:
                token = self._loadFromEnvironment(scheme_name, EnvVarKeys.TOKEN, source_name)  
                if not token:
                    return None
                        
                return BearerAuth(
                    type=AuthType.HTTP,
                    token=token
                )
            elif scheme.scheme == HttpSchemeType.BASIC:
                username = self._loadFromEnvironment(scheme_name, EnvVarKeys.USERNAME, source_name)
                password = self._loadFromEnvironment(scheme_name, EnvVarKeys.PASSWORD, source_name)
                if not username or not password:
                    return None
                        
                return BasicAuth(
                    type=AuthType.HTTP,
                    username=username,
                    password=password
                )
            else:
                # Generic HTTP auth
                auth_value = self._loadFromEnvironment(scheme_name, EnvVarKeys.AUTH_VALUE, source_name)
                if not auth_value:
                    return None
                        
                # Use BearerAuth as a fallback for generic HTTP auth
                return BearerAuth(
                    type=AuthType.HTTP,
                    token=auth_value
                )

        elif scheme.type == AuthType.OAUTH2:
            return self._resolve_oauth2_auth_value(scheme=scheme, scheme_name=scheme_name, source_name=source_name, scopes=scopes)
            
        elif scheme.type == AuthType.OPENID:
            # For OpenID, check for ID token
            id_token = self._loadFromEnvironment(scheme_name, EnvVarKeys.TOKEN, source_name)  
            if not id_token:
                return None
                    
            # Use OAuth2AccessTokenOnly for OpenID as well since they're similar
            return OAuth2AccessTokenOnly(
                type=AuthType.OPENID,
                access_token=id_token
            )
            
        elif scheme.type == AuthType.CUSTOM:
            # For custom auth, we need to check the scheme name
            # This is a simplification - in a real implementation, we would need to know what key to use
            # For now, we'll try to use the scheme name as the key
            auth_value = self._loadFromEnvironment(scheme_name, scheme.name, source_name)
            if not auth_value:
                return None
                    
            # Use ApiKeyAuth as a fallback for custom auth
            return ApiKeyAuth(
                type=AuthType.CUSTOM,
                api_key=auth_value
            )
            
        return None

    def _resolve_oauth2_auth_value(
        self, 
        scheme: OAuth2Scheme, 
        scheme_name: str, 
        source_name: str | None = None, 
        scopes: List[str] | None = None
    ) -> AuthValue | None:
        """
        Resolve authentication value for OAuth2 security scheme.
        
        Args:
            scheme: The OAuth2 security scheme
            scheme_name: Name of the security scheme
            source_name: Optional source name of the security scheme
            scopes: Optional list of scopes required for this authentication
            
        Returns:
            AuthValue if resolved, None otherwise
        """
        logger.debug(f"Resolving OAuth2 auth value for {scheme=}, {scheme_name=}, {source_name=}, {scopes=}")
        # Determine the flow type and create a modified scheme name
        flow_type = None
        if scheme.flows.client_credentials:
            flow_type = "clientCredentials"
        elif scheme.flows.authorization_code or scheme.flows.implicit:
            flow_type = "web"
        elif scheme.flows.password:
            flow_type = "password"
        else:
            flow_type = "default"
        
        # Create modified scheme name based on the flow type
        modified_scheme_name = f"{scheme_name}.{flow_type}"
        
        # Initialize access token
        access_token = None
        
        # For client credentials flow, try to obtain a token dynamically first
        if flow_type == "clientCredentials" and scheme.flows.client_credentials:
            # Get client ID and secret from environment variables
            client_id = self._loadFromEnvironment(modified_scheme_name, EnvVarKeys.CLIENT_ID, source_name)
            client_secret = self._loadFromEnvironment(modified_scheme_name, EnvVarKeys.CLIENT_SECRET, source_name)
            
            # Get token URL from the security scheme
            token_url = scheme.flows.client_credentials.token_url
            
            if client_id and client_secret and token_url:
                access_token = self._request_oauth_access_token(
                    token_url=token_url,
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=scopes,
                    scheme_name=scheme_name
                )
        
        # If we couldn't get a token dynamically, try to load a pre-configured one as fallback
        if not access_token:
            access_token = self._loadFromEnvironment(modified_scheme_name, EnvVarKeys.TOKEN, source_name)

        if not access_token:
            return None
                
        return OAuth2AccessTokenOnly(
            type=AuthType.OAUTH2,
            access_token=access_token
        )

    def _request_oauth_access_token(
        self, 
        token_url: str, 
        client_id: str, 
        client_secret: str, 
        scopes: List[str] | None = None,
        scheme_name: str = ""
    ) -> str | None:
        """
        Request an OAuth2 access token using client credentials flow.
        
        Args:
            token_url: The token endpoint URL
            client_id: The OAuth2 client ID
            client_secret: The OAuth2 client secret
            scopes: Optional list of scopes required for this authentication
            scheme_name: Name of the security scheme for logging purposes
            
        Returns:
            Access token if successful, None otherwise
        """
        try:
            # Prepare the request for client credentials grant
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }

            # Add scopes if available
            if scopes:
                scopes_str = " ".join(scopes)
                data["scope"] = scopes_str
            
            # Make the token request
            response = self._http_client.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                
                # Log success but not the actual token
                logger.info(f"Successfully obtained OAuth2 access token for {scheme_name}")
                return access_token
            else:
                logger.warning(f"Failed to obtain OAuth2 access token: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error obtaining OAuth2 access token: {str(e)}")
            
        return None

    def _loadFromEnvironment(
        self, 
        scheme_name: str, 
        mapping_key: str, 
        source_name: str | None = None
    ) -> str | None:
        """
        Load a value from environment variables.
        
        Args:
            scheme_name: Name of the security scheme
            mapping_key: Key to look up in the environment mappings
            source_name: Optional source name to construct composite key
            
        Returns:
            Value from environment if found, None otherwise
        """
        logger.debug(f"Loading from environment: {scheme_name=}, {mapping_key=}, {source_name=}")
        # First try with the direct scheme name
        env_var_name: str | None = self._env_mapping.get(scheme_name, {}).get(mapping_key)
        if env_var_name:
            logger.debug(f"Found env var name: {env_var_name=}")
            return os.getenv(env_var_name, default=None)

        # Try to find using source name as the outer key
        if source_name and source_name in self._env_mapping:
            logger.debug(f"Found source name: {source_name=}")
            source_mappings = self._env_mapping[source_name]
            if isinstance(source_mappings, dict) and scheme_name in source_mappings:
                logger.debug(f"Found scheme name: {scheme_name=}")
                scheme_mappings = source_mappings[scheme_name]
                if isinstance(scheme_mappings, dict) and mapping_key in scheme_mappings:
                    logger.debug(f"Found mapping key: {mapping_key=}")
                    env_var_name = scheme_mappings[mapping_key]
                    if env_var_name:
                        logger.debug(f"Found env var name: {env_var_name=}")
                        return os.getenv(env_var_name, default=None)

        return None

    def _get_security_scheme(self, scheme_name: str, source_name: str | None = None) -> SecurityScheme | None:
        """
        Get a security scheme by name and source name.
        
        Args:
            scheme_name: Name of the security scheme
            source_name: Source name of the security scheme
            
        Returns:
            SecurityScheme if found, None otherwise
        """
        # If source name is provided, try to find the scheme in that source
        if source_name and source_name in self._security_schemes:
            if scheme_name in self._security_schemes[source_name]:
                return self._security_schemes[source_name][scheme_name]
        
        # If not found with source name or no source name provided,
        # try to find the scheme in any source
        for _source, schemes in self._security_schemes.items():
            if scheme_name in schemes:
                return schemes[scheme_name]
                
        return None


def create_security_schemes_from_auth_requirements(auth_requirements: List[AuthRequirement]) -> Dict[str, Dict[str, SecurityScheme]]:
    """
    Convert AuthRequirement dictionaries to SecurityScheme objects.
    
    Returns:
        Dictionary mapping source descriptions to dictionaries of scheme names to SecurityScheme objects
    """
    security_schemes = {}
    for req in auth_requirements:
        scheme_name = req.get("security_scheme_name")
        if not scheme_name:
            continue
            
        auth_type = req.get("type")
        if not auth_type:
            continue
        
        # Get the source description, defaulting to a generic value if not available
        source_description = req.get("source_description_id", "default")
        
        # Initialize the source description dictionary if it doesn't exist
        if source_description not in security_schemes:
            security_schemes[source_description] = {}
            
        # Check if we already have a scheme with this name for this source
        existing_scheme = security_schemes[source_description].get(scheme_name)
        
        # Create the appropriate SecurityScheme based on auth_type
        if auth_type == AuthType.API_KEY:
            # Create API Key scheme
            scheme = ApiKeyScheme(
                type=AuthType.API_KEY,
                name=req.get("name", ""),
                description=req.get("description"),
                location=req.get("location", AuthLocation.HEADER),
                parameter_name=req.get("name", "")
            )
            
        elif auth_type == AuthType.HTTP:
            # Create HTTP scheme
            scheme = HttpAuthScheme(
                type=AuthType.HTTP,
                name=req.get("name", ""),
                description=req.get("description"),
                scheme=req.get("schemes", ["bearer"])[0] if req.get("schemes") else "bearer"
            )
            
        elif auth_type == AuthType.OAUTH2:
            # Create OAuth2 URLs
            auth_urls = req.get("auth_urls", {})
            oauth2_urls = OAuth2Urls(
                authorization=auth_urls.get("authorization"),
                token=auth_urls.get("token"),
                refresh=auth_urls.get("refresh")
            )
            
            # If we already have an OAuth2 scheme, we'll merge the flows
            if existing_scheme and existing_scheme.type == AuthType.OAUTH2:
                # Use the existing scheme and just update its flows
                scheme = existing_scheme
                
                # Create OAuth2 flows based on flow_type
                flow_type = req.get("flow_type")
                scopes_dict = {scope: f"Scope: {scope}" for scope in req.get("scopes", [])}
                
                # Update the appropriate flow based on flow_type
                if flow_type == OAuth2FlowType.IMPLICIT:
                    # Create implicit flow
                    scheme.flows.implicit = ImplicitFlow(
                        scopes=scopes_dict,
                        authorization_url=oauth2_urls.authorization or ""
                    )
                    
                elif flow_type == OAuth2FlowType.CLIENT_CREDENTIALS:
                    # Create client credentials flow
                    scheme.flows.client_credentials = ClientCredentialsFlow(
                        scopes=scopes_dict,
                        token_url=oauth2_urls.token or ""
                    )
                    
                elif flow_type == OAuth2FlowType.AUTHORIZATION_CODE:
                    # Create authorization code flow
                    scheme.flows.authorization_code = AuthorizationCodeFlow(
                        scopes=scopes_dict,
                        authorization_url=oauth2_urls.authorization or "",
                        token_url=oauth2_urls.token or "",
                        refresh_url=oauth2_urls.refresh
                    )
                    
                elif flow_type == OAuth2FlowType.PASSWORD:
                    # Create password flow
                    scheme.flows.password = PasswordFlow(
                        scopes=scopes_dict,
                        token_url=oauth2_urls.token or ""
                    )
                
                # Skip adding the scheme since we're just updating the existing one
                continue
            else:
                # Create a new OAuth2 scheme
                
                # Create OAuth2 flows based on flow_type
                flows = OAuth2Flows()
                flow_type = req.get("flow_type")
                scopes_dict = {scope: f"Scope: {scope}" for scope in req.get("scopes", [])}
                
                if flow_type == OAuth2FlowType.IMPLICIT:
                    # Create implicit flow
                    flows.implicit = ImplicitFlow(
                        scopes=scopes_dict,
                        authorization_url=oauth2_urls.authorization or ""
                    )
                    
                elif flow_type == OAuth2FlowType.CLIENT_CREDENTIALS:
                    # Create client credentials flow
                    flows.client_credentials = ClientCredentialsFlow(
                        scopes=scopes_dict,
                        token_url=oauth2_urls.token or ""
                    )
                    
                elif flow_type == OAuth2FlowType.AUTHORIZATION_CODE:
                    # Create authorization code flow
                    flows.authorization_code = AuthorizationCodeFlow(
                        scopes=scopes_dict,
                        authorization_url=oauth2_urls.authorization or "",
                        token_url=oauth2_urls.token or "",
                        refresh_url=oauth2_urls.refresh
                    )
                    
                elif flow_type == OAuth2FlowType.PASSWORD:
                    # Create password flow
                    flows.password = PasswordFlow(
                        scopes=scopes_dict,
                        token_url=oauth2_urls.token or ""
                    )
                    
                # Create the OAuth2 scheme with the flows
                scheme = OAuth2Scheme(
                    type=AuthType.OAUTH2,
                    name=req.get("name", ""),
                    description=req.get("description"),
                    flows=flows
                )
            
        elif auth_type == AuthType.OPENID:
            # Create OpenID scheme
            scheme = OpenIDScheme(
                type=AuthType.OPENID,
                name=req.get("name", ""),
                description=req.get("description"),
                openid_connect_url=req.get("openid_connect_url", "")
            )
            
        else:
            # Create custom scheme
            scheme = CustomScheme(
                type=AuthType.CUSTOM,
                name=req.get("name", ""),
                description=req.get("description")
            )
            
        security_schemes[source_description][scheme_name] = scheme
        
    return security_schemes
