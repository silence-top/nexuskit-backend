# domains/auth/exceptions.py — Auth domain exceptions
from common.exceptions.base import DomainError


class AuthDomainError(DomainError):
    status_code = 401


class UserAlreadyExistsError(AuthDomainError):
    status_code = 409


class InvalidCredentialsError(AuthDomainError):
    status_code = 401


class TokenMissingError(AuthDomainError):
    """No authentication token provided."""
    status_code = 401


class TokenInvalidError(AuthDomainError):
    """Token is invalid or expired."""
    status_code = 401


class TokenMisuseError(AuthDomainError):
    """Token used for wrong purpose (e.g. refresh token as access token)."""
    status_code = 401


class UserNotFoundError(AuthDomainError):
    status_code = 401


class UserBannedError(DomainError):
    """Account has been banned (403 not 401)."""
    status_code = 403


class TokenVersionMismatchError(AuthDomainError):
    """Token version mismatches DB — need to re-login."""
    status_code = 401


class TokenRevokedError(AuthDomainError):
    status_code = 403


class TokenRefreshConflictError(AuthDomainError):
    status_code = 429
