from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, engine
from app.core.exceptions import SRPException
from app.modules.academic.router import router as academic_router
from app.modules.auth.router import router as auth_router
from app.modules.users_mgmt.router import router as users_mgmt_router
from app.modules.imports.router import router as imports_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown routines."""
    # Startup: (Migrations will be handled explicitly via Alembic)
    yield
    # Shutdown: Dispose database connection pool cleanly
    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Student Result Portal - Official API for academic marks entry, validation, approval, and result publication.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SRPException)
async def srp_exception_handler(request: Request, exc: SRPException) -> JSONResponse:
    """Standardized JSON error handler for application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail,
            },
        },
    )


@app.get("/health", tags=["Health"])
def basic_health_check() -> dict:
    """Liveness probe: verifies the FastAPI application is alive."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def detailed_health_check(db: Session = Depends(get_db)) -> dict:
    """Readiness probe: verifies the API and database connection are responsive."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": settings.PROJECT_NAME,
                "database": db_status,
            },
        )

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }


# Mount Domain Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(academic_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_mgmt_router, prefix=settings.API_V1_PREFIX)
app.include_router(imports_router, prefix=settings.API_V1_PREFIX)




