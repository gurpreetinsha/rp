import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # Ensures all models are registered in Base.metadata
from app.database import Base, get_db
from app.main import app as fastapi_app
from app.modules.auth.models import User
from app.core.enums import UserRole
from app.core.security import hash_password, create_access_token

# In-memory SQLite engine for fast, isolated test execution
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db_session():
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Fixture providing a persisted administrator user."""
    admin = User(
        id=uuid.uuid4(),
        email="admin_fixture@institution.edu",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin Fixture",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_headers(admin_user):
    """Authorization headers for the fixture administrator."""
    token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_user(db_session):
    """Fixture providing a persisted teacher user."""
    teacher = User(
        id=uuid.uuid4(),
        email="teacher_fixture@institution.edu",
        hashed_password=hash_password("TeacherPass123!"),
        full_name="Teacher Fixture",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def teacher_headers(teacher_user):
    """Authorization headers for the fixture teacher."""
    token = create_access_token(data={"sub": str(teacher_user.id), "role": teacher_user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_user(db_session):
    """Fixture providing a persisted student user."""
    student = User(
        id=uuid.uuid4(),
        email="student_fixture@institution.edu",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Student Fixture",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


@pytest.fixture
def student_headers(student_user):
    """Authorization headers for the fixture student."""
    token = create_access_token(data={"sub": str(student_user.id), "role": student_user.role.value})
    return {"Authorization": f"Bearer {token}"}
