import pytest
from app.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.modules.auth.models import User
from app.core.enums import UserRole


def test_password_hashing_and_verification():
    """Verify bcrypt hashing generates non-reversible hashes that check correctly."""
    plain = "SuperSecretPassword123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_bootstrap_initial_admin(client):
    """Test bootstrapping the very first administrator on a clean system."""
    payload = {
        "email": "chief_admin@institution.edu",
        "password": "MasterAdminPass2026!",
        "full_name": "Chief Administrator",
    }
    res = client.post(f"{settings.API_V1_PREFIX}/auth/bootstrap-admin", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "chief_admin@institution.edu"
    assert data["role"] == UserRole.ADMIN.value
    assert data["full_name"] == "Chief Administrator"


def test_bootstrap_admin_forbidden_when_admin_exists(client, admin_user):
    """Test that once an admin exists, bootstrap-admin is blocked with 403 Forbidden."""
    payload = {
        "email": "impostor@institution.edu",
        "password": "Password123!",
        "full_name": "Second Admin",
    }
    res = client.post(f"{settings.API_V1_PREFIX}/auth/bootstrap-admin", json=payload)
    assert res.status_code == 403
    assert "already exists" in res.json()["error"]["message"]


def test_login_success(client, admin_user):
    """Test that authenticating with correct credentials returns a signed JWT token."""
    login_payload = {
        "email": admin_user.email,
        "password": "AdminPass123!",
    }
    res = client.post(f"{settings.API_V1_PREFIX}/auth/login", json=login_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == UserRole.ADMIN.value
    assert data["email"] == admin_user.email


def test_login_invalid_password(client, admin_user):
    """Test that login with incorrect password returns 401 with generic message."""
    login_payload = {
        "email": admin_user.email,
        "password": "WrongPassword!",
    }
    res = client.post(f"{settings.API_V1_PREFIX}/auth/login", json=login_payload)
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["error"]["message"]


def test_login_nonexistent_email(client):
    """Test that login with an unknown email returns 401 with generic message."""
    login_payload = {
        "email": "nonexistent@institution.edu",
        "password": "AnyPassword123!",
    }
    res = client.post(f"{settings.API_V1_PREFIX}/auth/login", json=login_payload)
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["error"]["message"]


def test_get_current_user_profile(client, admin_headers, admin_user):
    """Test retrieving current user profile using valid Bearer token."""
    res = client.get(f"{settings.API_V1_PREFIX}/auth/me", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == admin_user.email
    assert data["role"] == admin_user.role.value


def test_get_current_user_no_token_returns_401(client):
    """Test accessing protected profile endpoint without Authorization header."""
    res = client.get(f"{settings.API_V1_PREFIX}/auth/me")
    assert res.status_code == 401


def test_get_current_user_invalid_token_returns_401(client):
    """Test accessing protected endpoint with forged token returns 401."""
    res = client.get(
        f"{settings.API_V1_PREFIX}/auth/me",
        headers={"Authorization": "Bearer forged.invalid.token"},
    )
    assert res.status_code == 401


def test_role_enforcement_student_denied_admin_endpoint(client, student_headers):
    """Test that a Student token attempting to call an Admin-only endpoint receives 403 Forbidden."""
    payload = {"code": "FORBIDDEN_DEPT", "name": "Illegal Department"}
    res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json=payload,
        headers=student_headers,
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["error"]["message"]


def test_role_enforcement_teacher_denied_admin_endpoint(client, teacher_headers):
    """Test that a Teacher token attempting to call an Admin-only endpoint receives 403 Forbidden."""
    payload = {"code": "FORBIDDEN_DEPT", "name": "Illegal Department"}
    res = client.post(
        f"{settings.API_V1_PREFIX}/academic/departments",
        json=payload,
        headers=teacher_headers,
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["error"]["message"]


def test_inactive_user_cannot_authenticate(client, db_session):
    """Test that deactivated users cannot log in or use their tokens."""
    inactive_user = User(
        email="inactive@institution.edu",
        hashed_password=hash_password("InactivePass123!"),
        full_name="Inactive Person",
        role=UserRole.STUDENT,
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()

    login_res = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "inactive@institution.edu", "password": "InactivePass123!"},
    )
    assert login_res.status_code == 401
    assert "inactive" in login_res.json()["error"]["message"].lower()
