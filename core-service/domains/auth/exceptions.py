# domains/auth/exceptions.py — Auth domain exceptions
from nexuskit_sdk.codes import BizCode
from common.exceptions.base import DomainError


class AuthDomainError(DomainError):
    status_code = 401
    biz_code = BizCode.UNAUTHORIZED


class UserAlreadyExistsError(AuthDomainError):
    status_code = 409
    biz_code = BizCode.USER_EXISTS


class InvalidCredentialsError(AuthDomainError):
    status_code = 401
    biz_code = BizCode.INVALID_CREDS


class TokenMissingError(AuthDomainError):
    """No authentication token provided."""
    status_code = 401
    biz_code = BizCode.TOKEN_MISSING


class TokenInvalidError(AuthDomainError):
    """Token is invalid or expired."""
    status_code = 401
    biz_code = BizCode.TOKEN_INVALID


class TokenMisuseError(AuthDomainError):
    """Token used for wrong purpose (e.g. refresh token as access token)."""
    status_code = 401
    biz_code = BizCode.TOKEN_MISUSE


class UserNotFoundError(AuthDomainError):
    status_code = 401
    biz_code = BizCode.USER_NOT_FOUND


class UserBannedError(DomainError):
    """Account has been banned (403 not 401)."""
    status_code = 403
    biz_code = BizCode.USER_BANNED


class TokenVersionMismatchError(AuthDomainError):
    """Token version mismatches DB — need to re-login."""
    status_code = 401
    biz_code = BizCode.TOKEN_VERSION


class TokenRevokedError(AuthDomainError):
    """Token revoked (blacklisted after refresh/logout) or session expired (no valid RT)."""
    status_code = 403
    biz_code = BizCode.SESSION_EXPIRED


class TokenRefreshConflictError(AuthDomainError):
    """Concurrent refresh conflict — replay attack protection."""
    status_code = 429
    biz_code = BizCode.REFRESH_CONFLICT
