import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default: string | null;
}

interface TableSummary {
  name: string;
  row_count: number;
  columns: ColumnInfo[];
  primary_keys: string[];
}

interface TableDataResponse {
  table_name: string;
  total_rows: number;
  page: number;
  limit: number;
  columns: ColumnInfo[];
  primary_keys: string[];
  rows: Record<string, any>[];
}

interface DatabaseStudioProps {
  onNotify?: (msg: string, type: 'success' | 'danger') => void;
}

export const DatabaseStudio: React.FC<DatabaseStudioProps> = ({ onNotify }) => {
  const [viewMode, setViewMode] = useState<'explorer' | 'sql'>('explorer');

  // Tables Metadata
  const [tables, setTables] = useState<TableSummary[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [tableSearchFilter, setTableSearchFilter] = useState<string>('');
  const [loadingTables, setLoadingTables] = useState<boolean>(false);

  // Table Data & Pagination
  const [tableData, setTableData] = useState<TableDataResponse | null>(null);
  const [loadingData, setLoadingData] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(25);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [orderBy, setOrderBy] = useState<string>('');
  const [orderDir, setOrderDir] = useState<'asc' | 'desc'>('asc');

  // Row Modals
  const [editRowTarget, setEditRowTarget] = useState<Record<string, any> | null>(null);
  const [editRowFormData, setEditRowFormData] = useState<Record<string, any>>({});
  const [showInsertModal, setShowInsertModal] = useState<boolean>(false);
  const [insertFormData, setInsertFormData] = useState<Record<string, any>>({});
  const [deleteRowTarget, setDeleteRowTarget] = useState<Record<string, any> | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // SQL Console State
  const [sqlQuery, setSqlQuery] = useState<string>('SELECT * FROM users LIMIT 25;');
  const [sqlExecuting, setSqlExecuting] = useState<boolean>(false);
  const [sqlResult, setSqlResult] = useState<any | null>(null);
  const [sqlError, setSqlError] = useState<string | null>(null);

  const notify = useCallback(
    (msg: string, type: 'success' | 'danger') => {
      if (onNotify) {
        onNotify(msg, type);
      } else {
        alert(msg);
      }
    },
    [onNotify]
  );

  // Fetch Tables List
  const loadTables = useCallback(async () => {
    setLoadingTables(true);
    try {
      const data = await api.getDbTables();
      setTables(data);
      if (data.length > 0 && !selectedTable) {
        setSelectedTable(data[0].name);
      }
    } catch (err: any) {
      notify(err.message || 'Failed to load database tables', 'danger');
    } finally {
      setLoadingTables(false);
    }
  }, [notify, selectedTable]);

  useEffect(() => {
    loadTables();
  }, [loadTables]);

  // Fetch Rows for Selected Table
  const loadTableRows = useCallback(
    async (tblName: string, p = page, l = limit, q = searchQuery, ob = orderBy, od = orderDir) => {
      if (!tblName) return;
      setLoadingData(true);
      try {
        const res = await api.getDbTableRows(tblName, p, l, q, ob, od);
        setTableData(res);
      } catch (err: any) {
        notify(err.message || `Failed to fetch rows for table '${tblName}'`, 'danger');
        setTableData(null);
      } finally {
        setLoadingData(false);
      }
    },
    [notify, page, limit, searchQuery, orderBy, orderDir]
  );

  useEffect(() => {
    if (selectedTable) {
      setPage(1);
      setSearchQuery('');
      setOrderBy('');
      loadTableRows(selectedTable, 1, limit, '', '', 'asc');
    }
  }, [selectedTable, limit, loadTableRows]);

  const handleTableSelect = (tblName: string) => {
    setSelectedTable(tblName);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadTableRows(selectedTable, 1, limit, searchQuery, orderBy, orderDir);
  };

  const handleSort = (colName: string) => {
    const newDir = orderBy === colName && orderDir === 'asc' ? 'desc' : 'asc';
    setOrderBy(colName);
    setOrderDir(newDir);
    setPage(1);
    loadTableRows(selectedTable, 1, limit, searchQuery, colName, newDir);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    loadTableRows(selectedTable, newPage, limit, searchQuery, orderBy, orderDir);
  };

  // Open Edit Row Modal
  const openEditRow = (row: Record<string, any>) => {
    setEditRowTarget(row);
    setEditRowFormData({ ...row });
  };

  const handleUpdateRowSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editRowTarget || !tableData) return;

    const pkCol = tableData.primary_keys[0] || 'id';
    const rowId = String(editRowTarget[pkCol]);
    if (!rowId) {
      notify('Cannot update row without a primary key identifier', 'danger');
      return;
    }

    setActionLoading(true);
    try {
      await api.updateDbRow(selectedTable, rowId, editRowFormData);
      notify(`Row '${rowId}' in '${selectedTable}' updated successfully!`, 'success');
      setEditRowTarget(null);
      loadTableRows(selectedTable, page, limit, searchQuery, orderBy, orderDir);
      loadTables();
    } catch (err: any) {
      notify(err.message || 'Failed to update row', 'danger');
    } finally {
      setActionLoading(false);
    }
  };

  // Open Insert Modal
  const openInsertModal = () => {
    if (!tableData) return;
    const initial: Record<string, any> = {};
    tableData.columns.forEach((col) => {
      if (col.name !== 'created_at' && col.name !== 'updated_at') {
        initial[col.name] = '';
      }
    });
    setInsertFormData(initial);
    setShowInsertModal(true);
  };

  const handleInsertRowSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tableData) return;

    setActionLoading(true);
    try {
      // Clean up empty strings for optional fields
      const payload: Record<string, any> = {};
      Object.entries(insertFormData).forEach(([k, v]) => {
        if (v !== '' && v !== undefined) {
          payload[k] = v;
        }
      });

      await api.insertDbRow(selectedTable, payload);
      notify(`New record successfully inserted into '${selectedTable}'!`, 'success');
      setShowInsertModal(false);
      loadTableRows(selectedTable, page, limit, searchQuery, orderBy, orderDir);
      loadTables();
    } catch (err: any) {
      notify(err.message || 'Failed to insert row', 'danger');
    } finally {
      setActionLoading(false);
    }
  };

  // Delete Row
  const confirmDeleteRow = async () => {
    if (!deleteRowTarget || !tableData) return;
    const pkCol = tableData.primary_keys[0] || 'id';
    const rowId = String(deleteRowTarget[pkCol]);

    setActionLoading(true);
    try {
      await api.deleteDbRow(selectedTable, rowId);
      notify(`Record '${rowId}' deleted from '${selectedTable}'!`, 'success');
      setDeleteRowTarget(null);
      loadTableRows(selectedTable, page, limit, searchQuery, orderBy, orderDir);
      loadTables();
    } catch (err: any) {
      notify(err.message || 'Failed to delete row', 'danger');
    } finally {
      setActionLoading(false);
    }
  };

  // SQL Execution
  const handleExecuteSql = async () => {
    if (!sqlQuery.trim()) return;
    setSqlExecuting(true);
    setSqlError(null);
    setSqlResult(null);

    try {
      const res = await api.executeDbQuery(sqlQuery.trim());
      setSqlResult(res);
      notify(
        res.is_select
          ? `Executed in ${res.execution_time_ms}ms (${res.rows?.length || 0} rows returned)`
          : `Executed in ${res.execution_time_ms}ms (${res.rows_affected ?? 0} rows affected)`,
        'success'
      );
      loadTables();
    } catch (err: any) {
      setSqlError(err.message || 'SQL execution failed');
      notify(err.message || 'SQL execution failed', 'danger');
    } finally {
      setSqlExecuting(false);
    }
  };

  // Export Results to CSV
  const exportCsv = (rows: any[], columns: string[], filename: string) => {
    if (!rows || rows.length === 0) return;
    const headers = columns.join(',');
    const csvRows = rows.map((r) =>
      columns
        .map((col) => {
          const val = r[col];
          if (val === null || val === undefined) return '';
          const str = String(val).replace(/"/g, '""');
          return `"${str}"`;
        })
        .join(',')
    );
    const csvContent = [headers, ...csvRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredTables = tables.filter((t) =>
    t.name.toLowerCase().includes(tableSearchFilter.toLowerCase().trim())
  );

  const currentTableObj = tables.find((t) => t.name === selectedTable);
  const totalPages = tableData ? Math.ceil(tableData.total_rows / limit) || 1 : 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Studio Header Card */}
      <div
        className="glass-panel"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          borderLeft: '4px solid var(--accent-cyan)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.6rem' }}>🗄️</span>
            <div>
              <h2 style={{ fontSize: '1.4rem', margin: 0 }}>Database Studio & Live Administrator</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: 0 }}>
                Direct table browser, schema explorer, full record CRUD (Insert, Edit, Delete), and interactive SQL console.
              </p>
            </div>
          </div>
        </div>

        {/* View Toggle Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-surface-elevated)', padding: '0.3rem', borderRadius: 'var(--radius-md)' }}>
          <button
            className={`btn btn-sm ${viewMode === 'explorer' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ border: 'none', borderRadius: 'var(--radius-sm)' }}
            onClick={() => setViewMode('explorer')}
          >
            📑 Table Explorer & Records
          </button>
          <button
            className={`btn btn-sm ${viewMode === 'sql' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ border: 'none', borderRadius: 'var(--radius-sm)' }}
            onClick={() => setViewMode('sql')}
          >
            ⚡ SQL Query Console
          </button>
        </div>
      </div>

      {/* VIEW 1: TABLE EXPLORER */}
      {viewMode === 'explorer' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(240px, 300px) 1fr', gap: '1.5rem', alignItems: 'start' }}>
          {/* Table List Sidebar */}
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '780px', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Tables ({tables.length})
              </span>
              <button
                className="btn btn-secondary btn-sm"
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={loadTables}
                title="Reload Tables"
              >
                🔄
              </button>
            </div>

            <input
              type="text"
              className="form-input"
              style={{ fontSize: '0.85rem', padding: '0.4rem 0.75rem' }}
              placeholder="Filter tables..."
              value={tableSearchFilter}
              onChange={(e) => setTableSearchFilter(e.target.value)}
            />

            {loadingTables ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '1rem' }}>Loading tables...</p>
            ) : filteredTables.length === 0 ? (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', textAlign: 'center', padding: '1rem' }}>No matching tables</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {filteredTables.map((t) => {
                  const isSelected = t.name === selectedTable;
                  return (
                    <button
                      key={t.name}
                      onClick={() => handleTableSelect(t.name)}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.6rem 0.8rem',
                        borderRadius: 'var(--radius-sm)',
                        border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid transparent',
                        background: isSelected ? 'var(--bg-surface-hover)' : 'transparent',
                        color: isSelected ? 'var(--accent-cyan)' : 'var(--text-main)',
                        cursor: 'pointer',
                        textAlign: 'left',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.85rem',
                        transition: 'var(--transition-fast)',
                      }}
                    >
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {t.name}
                      </span>
                      <span
                        className="badge"
                        style={{
                          fontSize: '0.75rem',
                          padding: '0.15rem 0.5rem',
                          background: isSelected ? 'var(--accent-cyan)' : 'var(--bg-surface-elevated)',
                          color: isSelected ? '#000' : 'var(--text-muted)',
                        }}
                      >
                        {t.row_count}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Table Data Viewer & Editor */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Table Details & Toolbar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-mono)', margin: 0 }}>
                    {selectedTable || 'Select a table'}
                  </h3>
                  {currentTableObj && (
                    <span className="badge badge-info" style={{ fontSize: '0.8rem' }}>
                      {currentTableObj.row_count} rows total
                    </span>
                  )}
                  {tableData?.primary_keys && tableData.primary_keys.length > 0 && (
                    <span className="badge" style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.08)' }}>
                      PK: {tableData.primary_keys.join(', ')}
                    </span>
                  )}
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: '0.2rem 0 0 0' }}>
                  Showing {tableData ? tableData.rows.length : 0} records &bull; Columns: {tableData?.columns.length || 0}
                </p>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <button className="btn btn-primary btn-sm" onClick={openInsertModal} disabled={!selectedTable || loadingData}>
                  ➕ Insert Record
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => loadTableRows(selectedTable, page, limit, searchQuery, orderBy, orderDir)}
                  disabled={loadingData}
                  title="Refresh records"
                >
                  🔄
                </button>
                {tableData && tableData.rows.length > 0 && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() =>
                      exportCsv(
                        tableData.rows,
                        tableData.columns.map((c) => c.name),
                        `${selectedTable}_export`
                      )
                    }
                    title="Export current page to CSV"
                  >
                    📥 Export
                  </button>
                )}
              </div>
            </div>

            {/* Search and Limit Filters */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem', flex: 1, maxWidth: '450px' }}>
                <input
                  type="text"
                  className="form-input"
                  style={{ fontSize: '0.85rem' }}
                  placeholder="Search in all text/UUID fields..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button type="submit" className="btn btn-secondary btn-sm" disabled={loadingData}>
                  Search
                </button>
                {searchQuery && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      setSearchQuery('');
                      setPage(1);
                      loadTableRows(selectedTable, 1, limit, '', orderBy, orderDir);
                    }}
                  >
                    Clear
                  </button>
                )}
              </form>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                <span>Rows per page:</span>
                <select
                  className="form-select"
                  style={{ width: 'auto', padding: '0.25rem 0.6rem', fontSize: '0.85rem' }}
                  value={limit}
                  onChange={(e) => {
                    const l = parseInt(e.target.value);
                    setLimit(l);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>

            {/* Data Grid */}
            {loadingData ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>⏳</div>
                Loading records from <code>{selectedTable}</code>...
              </div>
            ) : !tableData || tableData.rows.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)', background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                <p style={{ margin: 0, fontSize: '0.95rem' }}>No records found in table <code>{selectedTable}</code>.</p>
                {searchQuery ? (
                  <button
                    className="btn btn-secondary btn-sm"
                    style={{ marginTop: '0.75rem' }}
                    onClick={() => {
                      setSearchQuery('');
                      setPage(1);
                      loadTableRows(selectedTable, 1, limit, '', orderBy, orderDir);
                    }}
                  >
                    Reset Search
                  </button>
                ) : (
                  <button className="btn btn-primary btn-sm" style={{ marginTop: '0.75rem' }} onClick={openInsertModal}>
                    ➕ Insert First Record
                  </button>
                )}
              </div>
            ) : (
              <div className="table-responsive" style={{ maxHeight: '560px', overflowY: 'auto' }}>
                <table className="data-table" style={{ fontSize: '0.85rem' }}>
                  <thead style={{ position: 'sticky', top: 0, zIndex: 2, background: 'var(--bg-surface-elevated)' }}>
                    <tr>
                      <th style={{ width: '110px', textAlign: 'center' }}>Actions</th>
                      {tableData.columns.map((col) => {
                        const isSorted = orderBy === col.name;
                        return (
                          <th
                            key={col.name}
                            onClick={() => handleSort(col.name)}
                            style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}
                            title={`Sort by ${col.name} (${col.type})`}
                          >
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                              {col.primary_key && <span>🔑</span>}
                              <strong>{col.name}</strong>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 400 }}>
                                ({col.type})
                              </span>
                              {isSorted && <span>{orderDir === 'asc' ? '▲' : '▼'}</span>}
                            </span>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.rows.map((row, idx) => {
                      const pkCol = tableData.primary_keys[0] || 'id';
                      const rowKey = row[pkCol] ?? idx;
                      return (
                        <tr key={String(rowKey)}>
                          <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                            <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => openEditRow(row)}
                                title="Edit / Change this row"
                              >
                                ✏️
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => setDeleteRowTarget(row)}
                                title="Delete / Remove this row"
                              >
                                🗑️
                              </button>
                            </div>
                          </td>
                          {tableData.columns.map((col) => {
                            const val = row[col.name];
                            return (
                              <td
                                key={col.name}
                                style={{
                                  fontFamily:
                                    col.primary_key || col.name.includes('_id') || col.name === 'id'
                                      ? 'var(--font-mono)'
                                      : 'inherit',
                                  maxWidth: '280px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                                title={val !== null && val !== undefined ? String(val) : 'NULL'}
                              >
                                {val === null ? (
                                  <span style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: '0.75rem' }}>
                                    null
                                  </span>
                                ) : typeof val === 'boolean' ? (
                                  <span className={`badge ${val ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.7rem' }}>
                                    {val ? 'TRUE' : 'FALSE'}
                                  </span>
                                ) : (
                                  String(val)
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Controls */}
            {tableData && tableData.total_rows > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Showing {(page - 1) * limit + 1} to {Math.min(page * limit, tableData.total_rows)} of {tableData.total_rows} records
                </span>

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    disabled={page <= 1 || loadingData}
                    onClick={() => handlePageChange(page - 1)}
                  >
                    ◀ Prev
                  </button>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-main)', padding: '0 0.5rem' }}>
                    Page {page} of {totalPages}
                  </span>
                  <button
                    className="btn btn-secondary btn-sm"
                    disabled={page >= totalPages || loadingData}
                    onClick={() => handlePageChange(page + 1)}
                  >
                    Next ▶
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* VIEW 2: INTERACTIVE SQL CONSOLE */}
      {viewMode === 'sql' && (
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.35rem' }}>Interactive SQL Query & Command Console</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: 0 }}>
              Execute arbitrary raw SQL statements (SELECT, INSERT, UPDATE, DELETE, DDL) directly against the database engine.
              All administrative operations are permanently logged to the audit trail.
            </p>
          </div>

          {/* Quick Query Templates */}
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
              Quick Templates
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {[
                { label: 'All Users', sql: 'SELECT * FROM users LIMIT 25;' },
                { label: 'Official Marks Ledger', sql: 'SELECT * FROM official_marks LIMIT 25;' },
                { label: 'Examination Sessions', sql: 'SELECT * FROM examination_sessions;' },
                { label: 'Active Students', sql: 'SELECT * FROM students WHERE is_active = 1 LIMIT 25;' },
                { label: 'Audit Trail', sql: 'SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 25;' },
                { label: 'All Tables Row Counts', sql: "SELECT name FROM sqlite_master WHERE type='table';" },
              ].map((tmpl) => (
                <button
                  key={tmpl.label}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
                  onClick={() => setSqlQuery(tmpl.sql)}
                >
                  {tmpl.label}
                </button>
              ))}
            </div>
          </div>

          {/* SQL Editor Area */}
          <div style={{ position: 'relative' }}>
            <textarea
              className="form-input"
              rows={6}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.95rem',
                lineHeight: 1.5,
                background: '#060911',
                border: '1px solid var(--border-medium)',
                color: '#7dd3fc',
                resize: 'vertical',
                tabSize: 2,
              }}
              value={sqlQuery}
              onChange={(e) => setSqlQuery(e.target.value)}
              onKeyDown={(e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                  e.preventDefault();
                  handleExecuteSql();
                }
              }}
              placeholder="Write SQL statement here... (e.g., SELECT * FROM users; or UPDATE ...)"
            />
            <div style={{ position: 'absolute', right: '12px', bottom: '12px', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
              Press Ctrl + Enter to run
            </div>
          </div>

          {/* Action Row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button className="btn btn-primary" onClick={handleExecuteSql} disabled={sqlExecuting || !sqlQuery.trim()}>
                {sqlExecuting ? '⏳ Executing...' : '▶️ Run SQL Command'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setSqlQuery('');
                  setSqlResult(null);
                  setSqlError(null);
                }}
              >
                Clear
              </button>
            </div>

            {sqlResult && sqlResult.is_select && sqlResult.rows && sqlResult.rows.length > 0 && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => exportCsv(sqlResult.rows, sqlResult.columns || [], 'sql_query_result')}
              >
                📥 Export Query to CSV
              </button>
            )}
          </div>

          {/* SQL Execution Error */}
          {sqlError && (
            <div
              style={{
                padding: '1rem',
                background: 'var(--danger-bg)',
                border: '1px solid var(--danger-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--danger)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.9rem',
              }}
            >
              ⚠️ {sqlError}
            </div>
          )}

          {/* SQL Execution Success & Result */}
          {sqlResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {/* Summary Stats Banner */}
              <div
                style={{
                  padding: '0.75rem 1rem',
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.85rem',
                }}
              >
                <span>
                  {sqlResult.is_select ? (
                    <>
                      ✅ Query returned <strong>{sqlResult.rows?.length || 0}</strong> records
                    </>
                  ) : (
                    <>
                      ✅ Command affected <strong>{sqlResult.rows_affected ?? 0}</strong> rows
                    </>
                  )}
                </span>
                <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                  Latency: {sqlResult.execution_time_ms} ms
                </span>
              </div>

              {/* Data Table for SELECT results */}
              {sqlResult.is_select && sqlResult.rows && sqlResult.rows.length > 0 && (
                <div className="table-responsive" style={{ maxHeight: '520px', overflowY: 'auto' }}>
                  <table className="data-table" style={{ fontSize: '0.85rem' }}>
                    <thead style={{ position: 'sticky', top: 0, zIndex: 2, background: 'var(--bg-surface-elevated)' }}>
                      <tr>
                        {sqlResult.columns?.map((col: string) => (
                          <th key={col} style={{ whiteSpace: 'nowrap' }}>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sqlResult.rows.map((row: any, i: number) => (
                        <tr key={i}>
                          {sqlResult.columns?.map((col: string) => {
                            const val = row[col];
                            return (
                              <td
                                key={col}
                                style={{
                                  fontFamily: col.includes('id') ? 'var(--font-mono)' : 'inherit',
                                  maxWidth: '280px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                                title={val !== null && val !== undefined ? String(val) : 'NULL'}
                              >
                                {val === null ? (
                                  <span style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: '0.75rem' }}>
                                    null
                                  </span>
                                ) : typeof val === 'boolean' ? (
                                  <span className={`badge ${val ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.7rem' }}>
                                    {val ? 'TRUE' : 'FALSE'}
                                  </span>
                                ) : (
                                  String(val)
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* MODAL: EDIT ROW */}
      {editRowTarget && tableData && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <div>
                <h3 style={{ margin: 0 }}>✏️ Edit Record in <code>{selectedTable}</code></h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
                  Modify values for this table record directly.
                </p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => setEditRowTarget(null)}>✕</button>
            </div>
            <form onSubmit={handleUpdateRowSubmit}>
              <div className="modal-body" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.85rem' }}>
                {tableData.columns.map((col) => {
                  const isPk = col.primary_key;
                  const isReadonly = isPk || col.name === 'created_at';
                  const val = editRowFormData[col.name];
                  const isBool = col.type.toLowerCase().includes('bool');

                  return (
                    <div className="form-group" key={col.name} style={{ marginBottom: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                        <label className="form-label" style={{ margin: 0, fontWeight: 600 }}>
                          {col.name} {isPk && '🔑 (Primary Key)'}
                        </label>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                          {col.type} {col.nullable ? '• nullable' : '• required'}
                        </span>
                      </div>

                      {isBool ? (
                        <select
                          className="form-select"
                          value={val === true || val === 'true' || val === 1 ? 'true' : 'false'}
                          onChange={(e) =>
                            setEditRowFormData({ ...editRowFormData, [col.name]: e.target.value === 'true' })
                          }
                          disabled={isReadonly}
                        >
                          <option value="true">TRUE</option>
                          <option value="false">FALSE</option>
                        </select>
                      ) : (
                        <input
                          type="text"
                          className="form-input"
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.85rem',
                            background: isReadonly ? 'rgba(0,0,0,0.3)' : undefined,
                            color: isReadonly ? 'var(--text-muted)' : undefined,
                          }}
                          value={val !== null && val !== undefined ? String(val) : ''}
                          onChange={(e) =>
                            setEditRowFormData({ ...editRowFormData, [col.name]: e.target.value })
                          }
                          disabled={isReadonly}
                          required={!col.nullable && !isReadonly}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditRowTarget(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={actionLoading}>
                  {actionLoading ? 'Saving...' : 'Save Direct Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: INSERT ROW */}
      {showInsertModal && tableData && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <div>
                <h3 style={{ margin: 0 }}>➕ Insert Record into <code>{selectedTable}</code></h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
                  Leave ID or auto-timestamps blank to have the database generate them automatically.
                </p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowInsertModal(false)}>✕</button>
            </div>
            <form onSubmit={handleInsertRowSubmit}>
              <div className="modal-body" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.85rem' }}>
                {tableData.columns
                  .filter((c) => c.name !== 'created_at' && c.name !== 'updated_at')
                  .map((col) => {
                    const isBool = col.type.toLowerCase().includes('bool');
                    const val = insertFormData[col.name];

                    return (
                      <div className="form-group" key={col.name} style={{ marginBottom: 0 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                          <label className="form-label" style={{ margin: 0, fontWeight: 600 }}>
                            {col.name} {col.primary_key && '🔑 (Auto-generates if blank)'}
                          </label>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                            {col.type} {col.nullable ? '• nullable' : '• required'}
                          </span>
                        </div>

                        {isBool ? (
                          <select
                            className="form-select"
                            value={val === false || val === 'false' ? 'false' : 'true'}
                            onChange={(e) =>
                              setInsertFormData({ ...insertFormData, [col.name]: e.target.value === 'true' })
                            }
                          >
                            <option value="true">TRUE</option>
                            <option value="false">FALSE</option>
                          </select>
                        ) : (
                          <input
                            type="text"
                            className="form-input"
                            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
                            value={val ?? ''}
                            onChange={(e) =>
                              setInsertFormData({ ...insertFormData, [col.name]: e.target.value })
                            }
                            placeholder={col.primary_key ? 'Optional (auto-generated if empty)' : `Enter ${col.name}`}
                            required={!col.nullable && !col.primary_key}
                          />
                        )}
                      </div>
                    );
                  })}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowInsertModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={actionLoading}>
                  {actionLoading ? 'Inserting...' : 'Insert Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: DELETE ROW CONFIRMATION */}
      {deleteRowTarget && tableData && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <h3 style={{ color: 'var(--danger)', margin: 0 }}>🗑️ Confirm Permanent Row Deletion</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setDeleteRowTarget(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ margin: 0, lineHeight: 1.5 }}>
                Are you sure you want to permanently delete this record from <code>{selectedTable}</code>?
              </p>
              <div
                style={{
                  marginTop: '1rem',
                  padding: '0.75rem',
                  background: 'rgba(0,0,0,0.3)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-sm)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8rem',
                  maxHeight: '160px',
                  overflowY: 'auto',
                }}
              >
                {JSON.stringify(deleteRowTarget, null, 2)}
              </div>
              <p style={{ marginTop: '0.75rem', color: 'var(--danger)', fontSize: '0.85rem' }}>
                ⚠️ Warning: Foreign keys or related records may be affected depending on database constraints.
              </p>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={() => setDeleteRowTarget(null)}>
                Cancel
              </button>
              <button type="button" className="btn btn-danger" onClick={confirmDeleteRow} disabled={actionLoading}>
                {actionLoading ? 'Deleting...' : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
