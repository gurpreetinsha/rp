from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.enums import UserRole
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest, TokenOut, UserOut, UserCreate, BootstrapAdminRequest
)
from app.modules.auth.service import AuthService
from app.modules.auth.dependencies import get_current_user, require_admin
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.get("/setup-status")
def get_setup_status(db: Session = Depends(get_db)):
    """Check if system has an administrator or needs initial setup."""
    has_admin = db.execute(select(User).where(User.role == UserRole.ADMIN)).first() is not None
    return {"needs_setup": not has_admin}


@router.post("/login", response_model=TokenOut)
def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive a signed JWT access token."""
    client_ip = request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "unknown")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    user = AuthService.authenticate_user(db, credentials.email, credentials.password, client_ip=client_ip)
    access_token = create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "name": user.full_name,
    })
    return TokenOut(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile and role information for the currently authenticated user."""
    return current_user


@router.post("/bootstrap-admin", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(data: BootstrapAdminRequest, db: Session = Depends(get_db)):
    """Bootstrap the initial system administrator. Permitted only if no admin exists."""
    return AuthService.bootstrap_admin(db, data)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    data: UserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only endpoint to create user accounts for students, teachers, or administrators."""
    return AuthService.create_user(db, data)
