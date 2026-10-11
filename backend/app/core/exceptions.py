"""
Core exception definitions for InsureChain VoiceGuard backend.
All exceptions provide safe, sanitized error representations.
"""


class InsureChainException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ConfigurationException(InsureChainException):
    """Raised when an environment variable or setting is missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=500)


class DatabaseException(InsureChainException):
    """Raised for sanitized database operational or connectivity failures."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message=message, status_code=status_code)


class MigrationException(InsureChainException):
    """Raised when database migration runner encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=500)


class IntegrationException(InsureChainException):
    """Raised for third-party integration configuration or initialization issues."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(message=f"{service} error: {message}", status_code=502)
        self.service = service


class AuthenticationException(InsureChainException):
    """Raised when authentication credentials or token are invalid or expired."""

    def __init__(self, message: str = "Invalid authentication credentials.") -> None:
        super().__init__(message=message, status_code=401)


class AuthorizationException(InsureChainException):
    """Raised when an authenticated user lacks permissions for an operation."""

    def __init__(self, message: str = "Access forbidden. Insufficient permissions.") -> None:
        super().__init__(message=message, status_code=403)


class ResourceNotFoundException(InsureChainException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Requested resource not found.") -> None:
        super().__init__(message=message, status_code=404)


# Alias for concise import
NotFoundException = ResourceNotFoundException


class ConflictException(InsureChainException):
    """Raised when an entity or resource already exists."""

    def __init__(self, message: str = "Resource conflict encountered.") -> None:
        super().__init__(message=message, status_code=409)


class ValidationException(InsureChainException):
    """Raised when input or state validation fails."""

    def __init__(self, message: str = "Validation failed.") -> None:
        super().__init__(message=message, status_code=422)

