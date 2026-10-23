from typing import Any, Optional
from fastapi import HTTPException, status


class SRPException(HTTPException):
    """Base application exception."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class UnauthorizedException(SRPException):
    def __init__(self, detail: str = "Invalid authentication credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(SRPException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundException(SRPException):
    def __init__(self, detail: str = "Requested resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(SRPException):
    def __init__(self, detail: str = "Resource conflict or duplicate entry"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


# Modern Starlette HTTP_422_UNPROCESSABLE_CONTENT with direct integer fallback
HTTP_422_CODE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class ValidationFailedException(SRPException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=HTTP_422_CODE, detail=detail)


ValidationException = ValidationFailedException
