import uuid
from typing import List, Callable
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.modules.auth.models import User
from app.core.enums import UserRole
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT access token from request Authorization header."""
    if not token:
        raise UnauthorizedException("Not authenticated")

    payload = decode_access_token(token)
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Invalid token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user identifier in token")

    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedException("User account not found")

    if not user.is_active:
        raise UnauthorizedException("User account is inactive")

    return user


def require_role(allowed_roles: List[UserRole]) -> Callable[[User], User]:
    """Dependency factory that verifies current authenticated user has an authorized role."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = ", ".join(r.value for r in allowed_roles)
            raise ForbiddenException(
                f"Access denied. Requires one of the following roles: {role_names}"
            )
        return current_user

    return role_checker


# Convenience role dependencies
require_admin = require_role([UserRole.ADMIN])
require_teacher = require_role([UserRole.TEACHER])
require_student = require_role([UserRole.STUDENT])
require_staff = require_role([UserRole.ADMIN, UserRole.TEACHER])
