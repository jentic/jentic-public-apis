from abc import ABC, abstractmethod
import logging

from oak_runner.auth.credentials.models import Credential

logger = logging.getLogger(__name__)

class CredentialValidator(ABC):
    """Abstract base class for credential validators."""
    
    @abstractmethod
    def validate(self, credential: Credential) -> bool:
        """Validate a credential."""
        raise NotImplementedError


class ValidCredentialValidator(CredentialValidator):
    """Validator that checks to see if we have a valid credential."""
    
    def validate(self, credential: Credential) -> bool:
        # Check if we have a security scheme and auth_value set, if not this isnt valid
        if not credential.security_scheme:
            logger.warning(f"Credential has no security scheme: {credential}")
            return False
        if not credential.auth_value:
            logger.warning(f"Credential has no auth value: {credential}")
            return False
        return True
