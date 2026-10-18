import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, BootstrapAdminRequest
from app.core.enums import UserRole
from app.core.security import hash_password, verify_password
from app.core.exceptions import UnauthorizedException, ConflictException, ForbiddenException


class AuthService:
    """Service handling user authentication and credential verification."""

    @staticmethod
    def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        return db.get(User, user_id)

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        normalized = email.strip().lower()
        return db.execute(select(User).where(User.email == normalized)).scalar_one_or_none()

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user by email and password; verify account is active."""
        user = AuthService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            # Generic response to prevent account enumeration
            raise UnauthorizedException("Incorrect email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive. Please contact the administrator.")

        return user

    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:
        """Create a new user with hashed credentials."""
        existing = AuthService.get_user_by_email(db, data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' already exists")

        user = User(
            email=data.email.strip().lower(),
            hashed_password=hash_password(data.password),
            full_name=data.name if hasattr(data, "name") else data.full_name.strip(),
            role=data.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def bootstrap_admin(db: Session, data: BootstrapAdminRequest) -> User:
        """Bootstrap the initial administrator if no administrator exists in the system."""
        existing_admin = db.execute(
            select(User).where(User.role == UserRole.ADMIN)
        ).scalar_one_or_none()

        if existing_admin:
            raise ForbiddenException("Administrator account already exists. Use standard admin login.")

        # Check if email is in use
        existing_email = AuthService.get_user_by_email(db, data.email)
        if existing_email:
            raise ConflictException(f"Account with email '{data.email}' already exists")

        admin_user = User(
            email=data.email.strip().lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        return admin_user
