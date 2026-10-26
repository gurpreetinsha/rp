import uuid
import time
import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, text, Table, MetaData
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.audit.service import AuditService
from app.modules.database_admin.schemas import (
    ColumnInfo,
    TableSummary,
    TableDataResponse,
    SqlQueryResponse,
)


def serialize_value(val: Any) -> Any:
    """Helper to convert any Python DB value into a JSON-serializable representation."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except UnicodeDecodeError:
            return val.hex()
    if hasattr(val, "value"):  # Enums
        return val.value
    return val


def clean_row_dict(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    return {k: serialize_value(v) for k, v in row_dict.items()}


class DatabaseAdminService:
    """Provides high-level metadata inspection and direct CRUD/query execution across all tables."""

    @staticmethod
    def get_tables(db: Session) -> List[TableSummary]:
        bind = db.get_bind()
        inspector = inspect(bind)
        table_names = sorted(inspector.get_table_names())

        summaries: List[TableSummary] = []
        for tbl in table_names:
            # Skip internal alembic version table if desired or include it
            columns_raw = inspector.get_columns(tbl)
            pk_constraint = inspector.get_pk_constraint(tbl)
            pk_cols = pk_constraint.get("constrained_columns", []) if pk_constraint else []

            columns: List[ColumnInfo] = []
            for col in columns_raw:
                columns.append(
                    ColumnInfo(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=bool(col.get("nullable", True)),
                        primary_key=col["name"] in pk_cols,
                        default=str(col.get("default")) if col.get("default") is not None else None,
                    )
                )

            # Row count
            try:
                count_res = db.execute(text(f'SELECT COUNT(*) FROM "{tbl}"')).scalar()
                row_count = int(count_res) if count_res is not None else 0
            except Exception:
                row_count = 0

            summaries.append(
                TableSummary(
                    name=tbl,
                    row_count=row_count,
                    columns=columns,
                    primary_keys=pk_cols,
                )
            )

        return summaries

    @staticmethod
    def get_table_rows(
        db: Session,
        table_name: str,
        page: int = 1,
        limit: int = 25,
        search: Optional[str] = None,
        order_by: Optional[str] = None,
        order_dir: str = "asc",
    ) -> TableDataResponse:
        bind = db.get_bind()
        inspector = inspect(bind)
        table_names = inspector.get_table_names()
        if table_name not in table_names:
            raise NotFoundException(f"Table '{table_name}' does not exist in the database")

        columns_raw = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_cols = pk_constraint.get("constrained_columns", []) if pk_constraint else []

        columns: List[ColumnInfo] = [
            ColumnInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=bool(col.get("nullable", True)),
                primary_key=col["name"] in pk_cols,
                default=str(col.get("default")) if col.get("default") is not None else None,
            )
            for col in columns_raw
        ]

        # Valid order_by column
        col_names = [c["name"] for c in columns_raw]
        safe_order_by = order_by if order_by and order_by in col_names else (pk_cols[0] if pk_cols else col_names[0])
        safe_order_dir = "DESC" if order_dir.lower() == "desc" else "ASC"

        # Search filter across string columns
        where_clauses = []
        params: Dict[str, Any] = {}
        if search and search.strip():
            search_param = f"%{search.strip()}%"
            params["search_term"] = search_param
            text_col_conditions = []
            for col in columns_raw:
                type_str = str(col["type"]).lower()
                if any(t in type_str for t in ["char", "text", "string", "uuid"]):
                    text_col_conditions.append(f'CAST("{col["name"]}" AS TEXT) LIKE :search_term')
            if text_col_conditions:
                where_clauses.append(f"({' OR '.join(text_col_conditions)})")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Total count query
        count_query = text(f'SELECT COUNT(*) FROM "{table_name}" {where_sql}')
        total_rows = db.execute(count_query, params).scalar() or 0

        # Paginated rows query
        offset = max(0, (page - 1) * limit)
        data_query = text(
            f'SELECT * FROM "{table_name}" {where_sql} '
            f'ORDER BY "{safe_order_by}" {safe_order_dir} '
            f'LIMIT :limit OFFSET :offset'
        )
        params["limit"] = limit
        params["offset"] = offset

        result = db.execute(data_query, params)
        rows = [clean_row_dict(dict(row._mapping)) for row in result]

        return TableDataResponse(
            table_name=table_name,
            total_rows=total_rows,
            page=page,
            limit=limit,
            columns=columns,
            primary_keys=pk_cols,
            rows=rows,
        )

    @staticmethod
    def insert_row(
        db: Session,
        table_name: str,
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        bind = db.get_bind()
        inspector = inspect(bind)
        if table_name not in inspector.get_table_names():
            raise NotFoundException(f"Table '{table_name}' does not exist")

        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=bind)

        # Prepare typed data
        insert_data: Dict[str, Any] = {}
        for col in table.columns:
            if col.name in data:
                val = data[col.name]
                if val == "" and col.nullable:
                    val = None
                elif val is not None:
                    type_str = str(col.type).lower()
                    if "uuid" in type_str and isinstance(val, str):
                        try:
                            val = uuid.UUID(val)
                        except ValueError:
                            pass
                    elif "bool" in type_str:
                        val = val in (True, "true", "True", 1, "1")
                    elif "int" in type_str and not isinstance(val, int):
                        try:
                            val = int(val)
                        except (ValueError, TypeError):
                            pass
                    elif "float" in type_str and not isinstance(val, float):
                        try:
                            val = float(val)
                        except (ValueError, TypeError):
                            pass
                insert_data[col.name] = val

        now = datetime.datetime.now(datetime.timezone.utc)
        if "created_at" in table.columns and "created_at" not in insert_data:
            insert_data["created_at"] = now
        if "updated_at" in table.columns and "updated_at" not in insert_data:
            insert_data["updated_at"] = now
        if "id" in table.columns and ("id" not in insert_data or not insert_data["id"]):
            if "uuid" in str(table.columns["id"].type).lower():
                insert_data["id"] = uuid.uuid4()

        try:
            stmt = table.insert().values(**insert_data)
            db.execute(stmt)
            db.commit()
        except Exception as e:
            db.rollback()
            raise BadRequestException(f"Failed to insert row into '{table_name}': {str(e)}")

        AuditService.log(
            db,
            user_id=user_id,
            action="DB_INSERT_ROW",
            entity_type=table_name,
            entity_id=str(insert_data.get("id", "new")),
            details={"inserted_data": clean_row_dict(insert_data)},
        )
        db.commit()

        return clean_row_dict(insert_data)

    @staticmethod
    def update_row(
        db: Session,
        table_name: str,
        row_id: str,
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        bind = db.get_bind()
        inspector = inspect(bind)
        if table_name not in inspector.get_table_names():
            raise NotFoundException(f"Table '{table_name}' does not exist")

        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_cols = pk_constraint.get("constrained_columns", []) if pk_constraint else []
        if not pk_cols:
            raise BadRequestException(f"Table '{table_name}' has no primary key defined")
        pk_col_name = pk_cols[0]

        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=bind)
        pk_column = table.columns[pk_col_name]

        # Convert row_id to proper type
        parsed_row_id: Any = row_id
        if "uuid" in str(pk_column.type).lower():
            try:
                parsed_row_id = uuid.UUID(row_id)
            except ValueError:
                pass
        elif "int" in str(pk_column.type).lower():
            try:
                parsed_row_id = int(row_id)
            except ValueError:
                pass

        # Prepare update dict
        update_data: Dict[str, Any] = {}
        for col in table.columns:
            if col.name in data and col.name != pk_col_name:
                val = data[col.name]
                if val == "" and col.nullable:
                    val = None
                elif val is not None:
                    type_str = str(col.type).lower()
                    if "uuid" in type_str and isinstance(val, str):
                        try:
                            val = uuid.UUID(val)
                        except ValueError:
                            pass
                    elif "bool" in type_str:
                        val = val in (True, "true", "True", 1, "1")
                    elif "int" in type_str and not isinstance(val, int):
                        try:
                            val = int(val)
                        except (ValueError, TypeError):
                            pass
                    elif "float" in type_str and not isinstance(val, float):
                        try:
                            val = float(val)
                        except (ValueError, TypeError):
                            pass
                update_data[col.name] = val

        if "updated_at" in table.columns and "updated_at" not in update_data:
            update_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)

        if not update_data:
            raise BadRequestException("No updatable fields provided")

        try:
            stmt = table.update().where(pk_column == parsed_row_id).values(**update_data)
            res = db.execute(stmt)
            if res.rowcount == 0:
                raise NotFoundException(f"Record with {pk_col_name}='{row_id}' not found in '{table_name}'")
            db.commit()
        except NotFoundException:
            raise
        except Exception as e:
            db.rollback()
            raise BadRequestException(f"Failed to update row in '{table_name}': {str(e)}")

        AuditService.log(
            db,
            user_id=user_id,
            action="DB_UPDATE_ROW",
            entity_type=table_name,
            entity_id=str(row_id),
            details={"updated_fields": clean_row_dict(update_data)},
        )
        db.commit()

        # Fetch updated row
        fetch_stmt = table.select().where(pk_column == parsed_row_id)
        updated_row = db.execute(fetch_stmt).first()
        return clean_row_dict(dict(updated_row._mapping)) if updated_row else clean_row_dict(update_data)

    @staticmethod
    def delete_row(
        db: Session,
        table_name: str,
        row_id: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> None:
        bind = db.get_bind()
        inspector = inspect(bind)
        if table_name not in inspector.get_table_names():
            raise NotFoundException(f"Table '{table_name}' does not exist")

        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_cols = pk_constraint.get("constrained_columns", []) if pk_constraint else []
        if not pk_cols:
            raise BadRequestException(f"Table '{table_name}' has no primary key defined")
        pk_col_name = pk_cols[0]

        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=bind)
        pk_column = table.columns[pk_col_name]

        parsed_row_id: Any = row_id
        if "uuid" in str(pk_column.type).lower():
            try:
                parsed_row_id = uuid.UUID(row_id)
            except ValueError:
                pass
        elif "int" in str(pk_column.type).lower():
            try:
                parsed_row_id = int(row_id)
            except ValueError:
                pass

        try:
            stmt = table.delete().where(pk_column == parsed_row_id)
            res = db.execute(stmt)
            if res.rowcount == 0:
                raise NotFoundException(f"Record with {pk_col_name}='{row_id}' not found in '{table_name}'")
            db.commit()
        except NotFoundException:
            raise
        except Exception as e:
            db.rollback()
            raise BadRequestException(f"Failed to delete row from '{table_name}': {str(e)}")

        AuditService.log(
            db,
            user_id=user_id,
            action="DB_DELETE_ROW",
            entity_type=table_name,
            entity_id=str(row_id),
            details={"table": table_name},
        )
        db.commit()

    @staticmethod
    def execute_sql(
        db: Session,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> SqlQueryResponse:
        clean_query = query.strip()
        if not clean_query:
            raise BadRequestException("Query string cannot be empty")

        start_time = time.perf_counter()
        try:
            result = db.execute(text(clean_query), params or {})
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if result.returns_rows:
                columns = list(result.keys())
                # Cap maximum returned rows at 1000 for browser safety
                raw_rows = result.fetchmany(1000)
                rows = [clean_row_dict(dict(r._mapping)) for r in raw_rows]
                return SqlQueryResponse(
                    query=clean_query,
                    is_select=True,
                    execution_time_ms=execution_time_ms,
                    columns=columns,
                    rows=rows,
                )
            else:
                rows_affected = result.rowcount
                db.commit()

                AuditService.log(
                    db,
                    user_id=user_id,
                    action="DB_EXECUTE_SQL",
                    entity_type="database",
                    entity_id="sql_execution",
                    details={"query": clean_query, "rows_affected": rows_affected},
                )
                db.commit()

                return SqlQueryResponse(
                    query=clean_query,
                    is_select=False,
                    execution_time_ms=execution_time_ms,
                    rows_affected=rows_affected,
                )
        except Exception as e:
            db.rollback()
            raise BadRequestException(f"SQL Execution Error: {str(e)}")
