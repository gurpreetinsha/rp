"""Script to reset the database to a clean, empty state without demo data."""

from app.database import engine, Base
import app.models


def reset_database():
    print("[RESET] Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("[RESET] Creating fresh database schema (clean slate, 0 users)...")
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] Database is completely clean and ready for real institutional onboarding!")


if __name__ == "__main__":
    reset_database()
