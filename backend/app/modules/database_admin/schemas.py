import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool
    default: Optional[str] = None


class TableSummary(BaseModel):
    name: str
    row_count: int
    columns: List[ColumnInfo]
    primary_keys: List[str]


class TableDataResponse(BaseModel):
    table_name: str
    total_rows: int
    page: int
    limit: int
    columns: List[ColumnInfo]
    primary_keys: List[str]
    rows: List[Dict[str, Any]]


class RowDataPayload(BaseModel):
    data: Dict[str, Any]


class SqlQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Raw SQL query to execute")
    params: Optional[Dict[str, Any]] = None


class SqlQueryResponse(BaseModel):
    query: str
    is_select: bool
    execution_time_ms: float
    rows_affected: Optional[int] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
