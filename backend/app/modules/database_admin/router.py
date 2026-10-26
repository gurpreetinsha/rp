from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.dependencies import require_admin
from app.modules.database_admin.service import DatabaseAdminService
from app.modules.database_admin.schemas import (
    TableSummary,
    TableDataResponse,
    RowDataPayload,
    SqlQueryRequest,
    SqlQueryResponse,
)

router = APIRouter(prefix="/database", tags=["Database Administration"])


@router.get("/tables", response_model=List[TableSummary])
def get_tables(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: list all database tables with schema and row counts."""
    return DatabaseAdminService.get_tables(db)


@router.get("/tables/{table_name}/rows", response_model=TableDataResponse)
def get_table_rows(
    table_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    search: Optional[str] = Query(None),
    order_by: Optional[str] = Query(None),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: fetch paginated rows from a specific database table with search and sort."""
    return DatabaseAdminService.get_table_rows(
        db=db,
        table_name=table_name,
        page=page,
        limit=limit,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.post("/tables/{table_name}/rows", status_code=status.HTTP_201_CREATED)
def insert_table_row(
    table_name: str,
    payload: RowDataPayload,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: insert a new row directly into any database table."""
    return DatabaseAdminService.insert_row(
        db=db,
        table_name=table_name,
        data=payload.data,
        user_id=current_admin.id,
    )


@router.put("/tables/{table_name}/rows/{row_id}")
def update_table_row(
    table_name: str,
    row_id: str,
    payload: RowDataPayload,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: update an existing row in any table by primary key."""
    return DatabaseAdminService.update_row(
        db=db,
        table_name=table_name,
        row_id=row_id,
        data=payload.data,
        user_id=current_admin.id,
    )


@router.delete("/tables/{table_name}/rows/{row_id}")
def delete_table_row(
    table_name: str,
    row_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: delete a row from any table by primary key."""
    DatabaseAdminService.delete_row(
        db=db,
        table_name=table_name,
        row_id=row_id,
        user_id=current_admin.id,
    )
    return {"success": True, "message": f"Row '{row_id}' deleted from table '{table_name}'"}


@router.post("/query", response_model=SqlQueryResponse)
def execute_sql_query(
    payload: SqlQueryRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: execute arbitrary SQL statement against the active database."""
    return DatabaseAdminService.execute_sql(
        db=db,
        query=payload.query,
        params=payload.params,
        user_id=current_admin.id,
    )
