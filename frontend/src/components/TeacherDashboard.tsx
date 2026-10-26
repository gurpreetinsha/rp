import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

export const TeacherDashboard: React.FC = () => {
  const [assignments, setAssignments] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [pastBatches, setPastBatches] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [selectedCourse, setSelectedCourse] = useState<string>('');
  const [maxMarks, setMaxMarks] = useState<number>(100);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [uploading, setUploading] = useState<boolean>(false);
  const [batchResult, setBatchResult] = useState<any | null>(null);
  const [stagedRows, setStagedRows] = useState<any[]>([]);
  const [loadingRows, setLoadingRows] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [asgn, sess, batches] = await Promise.all([
        api.getTeacherAssignments(),
        api.getSessions(),
        api.listBatches(),
      ]);
      setAssignments(asgn);
      setSessions(sess);
      setPastBatches(batches);
      if (sess.length > 0) setSelectedSession((prev) => prev || sess[0].id);
      if (asgn.length > 0) setSelectedCourse((prev) => prev || asgn[0].course_id);
    } catch (err: any) {
      setError(err.message || 'Failed to load teacher dashboard data.');
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
      setBatchResult(null);
      setStagedRows([]);
    }
  };

  const loadBatchRows = async (batchId: string) => {
    setLoadingRows(true);
    try {
      const rows = await api.getBatchRows(batchId);
      setStagedRows(rows);
    } catch (err: any) {
      setError(err.message || 'Failed to load staged rows.');
    } finally {
      setLoadingRows(false);
    }
  };

  const handleInspectBatch = async (batch: any) => {
    setBatchResult(batch);
    await loadBatchRows(batch.id);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a valid CSV file to upload.');
      return;
    }
    if (!selectedSession || !selectedCourse) {
      setError('Please select both an examination session and a course.');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);
    setStagedRows([]);
    try {
      const result = await api.uploadCsv(selectedSession, selectedCourse, maxMarks, selectedFile);
      setBatchResult(result);
      if (result.status === 'PENDING_APPROVAL') {
        setSuccessMsg(`CSV validated successfully! ${result.total_rows} student record(s) queued for admin approval.`);
      } else {
        setError(`CSV validation failed with ${result.error_rows} error(s). Please review the errors below.`);
      }
      await loadBatchRows(result.id);
      // Refresh batch history
      const batches = await api.listBatches();
      setPastBatches(batches);
    } catch (err: any) {
      setError(err.message || 'CSV submission failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.4rem' }}>Faculty Marks Submission Portal</h1>
        <p style={{ color: 'var(--text-muted)' }}>
          Upload student examination marks for your assigned courses. Submissions are rigorously validated before being queued for administrative review.
        </p>
      </div>

      {error && (
        <div style={{
          padding: '1rem',
          background: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--danger)',
          marginBottom: '1.5rem',
        }}>
          ⚠️ {error}
        </div>
      )}

      {successMsg && (
        <div style={{
          padding: '1rem',
          background: 'var(--success-bg)',
          border: '1px solid var(--success-border)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--success)',
          marginBottom: '1.5rem',
        }}>
          ✅ {successMsg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Course Assignment Overview */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem' }}>📚 Your Assigned Courses</h3>
          {assignments.length === 0 ? (
            <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem' }}>No course assignments assigned currently.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {assignments.map((asgn) => (
                <div key={asgn.id} style={{
                  padding: '0.75rem 1rem',
                  background: 'var(--bg-surface-elevated)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{asgn.course_code} - {asgn.course_name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Session: {asgn.session_name}</div>
                  </div>
                  <span className="badge badge-accent">Credits: {asgn.credits || '—'}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* CSV Upload Form */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem' }}>📤 Submit Marks Batch</h3>
          <form onSubmit={handleUpload}>
            <div className="form-group">
              <label className="form-label">Examination Session</label>
              <select
                className="form-select"
                value={selectedSession}
                onChange={(e) => setSelectedSession(e.target.value)}
                required
              >
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.academic_year})</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Course</label>
              <select
                className="form-select"
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                required
              >
                {assignments.map((a) => (
                  <option key={a.course_id} value={a.course_id}>
                    {a.course_code} - {a.course_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Maximum Evaluation Marks</label>
              <input
                type="number"
                className="form-input"
                min="1"
                max="1000"
                value={maxMarks}
                onChange={(e) => setMaxMarks(Number(e.target.value))}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Select CSV File</label>
              <input
                type="file"
                accept=".csv"
                className="form-input"
                onChange={handleFileChange}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '0.5rem' }}
              disabled={uploading}
            >
              {uploading ? 'Validating CSV...' : 'Validate & Upload Marks'}
            </button>
          </form>
        </div>
      </div>

      {/* Upload Batch Review & Staged Rows */}
      {batchResult && (
        <div className="glass-panel" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <h3 style={{ fontSize: '1.25rem' }}>Batch Review: {batchResult.file_name}</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Total: <strong>{batchResult.total_rows}</strong> | Valid: <strong style={{ color: 'var(--success)' }}>{batchResult.valid_rows}</strong> | Errors: <strong style={{ color: 'var(--danger)' }}>{batchResult.error_rows}</strong> | Max Marks: {batchResult.max_marks}
              </p>
              {batchResult.rejection_reason && (
                <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                  Rejection Reason: {batchResult.rejection_reason}
                </p>
              )}
            </div>
            <span className={`badge ${batchResult.status === 'IMPORTED' ? 'badge-pass' : batchResult.status === 'PENDING_APPROVAL' ? 'badge-accent' : 'badge-fail'}`}>
              {batchResult.status}
            </span>
          </div>

          {/* Sample Errors Summary */}
          {batchResult.sample_errors && batchResult.sample_errors.length > 0 && (
            <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'var(--danger-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--danger-border)' }}>
              <h4 style={{ color: 'var(--danger)', marginBottom: '0.5rem', fontSize: '0.95rem' }}>Validation Errors Found</h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--danger)', fontSize: '0.85rem' }}>
                {batchResult.sample_errors.map((err: any, idx: number) => (
                  <li key={idx} style={{ marginBottom: '0.25rem' }}>
                    Row {err.row_number} ({err.registration_number}): {
                      Array.isArray(err.errors)
                        ? err.errors.map((e: any) => e.message || e.code).join('; ')
                        : JSON.stringify(err.errors)
                    }
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Staged Rows Detail Table */}
          {loadingRows ? (
            <p style={{ color: 'var(--text-muted)' }}>Loading staged rows...</p>
          ) : stagedRows.length > 0 ? (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Registration #</th>
                    <th>Marks Entered</th>
                    <th>Absent?</th>
                    <th>Validation Status</th>
                    <th>Error Details</th>
                  </tr>
                </thead>
                <tbody>
                  {stagedRows.map((row: any) => (
                    <tr key={row.row_number}>
                      <td>{row.row_number}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.raw_registration_number}</td>
                      <td>{row.is_absent ? <span style={{ color: 'var(--warning)' }}>AB</span> : row.raw_marks_obtained}</td>
                      <td>{row.is_absent ? 'YES' : 'NO'}</td>
                      <td>
                        <span className={`badge ${row.is_valid ? 'badge-pass' : 'badge-fail'}`}>
                          {row.is_valid ? 'VALID' : 'INVALID'}
                        </span>
                      </td>
                      <td style={{ color: row.is_valid ? 'var(--text-muted)' : 'var(--danger)', fontSize: '0.85rem' }}>
                        {row.is_valid
                          ? 'OK'
                          : Array.isArray(row.validation_errors)
                            ? row.validation_errors.map((e: any) => e.message).join('; ')
                            : 'Error'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      )}

      {/* Submission History Table */}
      <div className="glass-panel">
        <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem' }}>📋 Your Submission History</h3>
        {pastBatches.length === 0 ? (
          <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem' }}>No upload batches submitted yet.</p>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Total Rows</th>
                  <th>Valid</th>
                  <th>Errors</th>
                  <th>Status</th>
                  <th>Uploaded At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {pastBatches.map((b) => (
                  <tr key={b.id}>
                    <td style={{ fontWeight: 500 }}>{b.file_name}</td>
                    <td>{b.total_rows}</td>
                    <td style={{ color: 'var(--success)' }}>{b.valid_rows}</td>
                    <td style={{ color: b.error_rows > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>{b.error_rows}</td>
                    <td>
                      <span className={`badge ${b.status === 'IMPORTED' ? 'badge-pass' : b.status === 'PENDING_APPROVAL' ? 'badge-accent' : 'badge-fail'}`}>
                        {b.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {new Date(b.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.25rem 0.6rem', fontSize: '0.8rem' }}
                        onClick={() => handleInspectBatch(b)}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
