import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

export const TeacherDashboard: React.FC = () => {
  const [assignments, setAssignments] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [selectedCourse, setSelectedCourse] = useState<string>('');
  const [maxMarks, setMaxMarks] = useState<number>(100);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [uploading, setUploading] = useState<boolean>(false);
  const [batchResult, setBatchResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [asgn, sess] = await Promise.all([
        api.getTeacherAssignments(),
        api.getSessions(),
      ]);
      setAssignments(asgn);
      setSessions(sess);
      if (sess.length > 0) setSelectedSession((prev) => prev || sess[0].id);
      if (asgn.length > 0) setSelectedCourse((prev) => prev || asgn[0].course_id);
    } catch (err: any) {
      setError(err.message || 'Failed to load teacher assignments.');
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
    }
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
    try {
      const result = await api.uploadCsv(selectedSession, selectedCourse, maxMarks, selectedFile);
      setBatchResult(result);
      if (result.status === 'PENDING_APPROVAL') {
        setSuccessMsg(`CSV validated successfully! ${result.total_rows} student record(s) queued for admin approval.`);
      } else {
        setError(`CSV validation failed with ${result.error_count} error(s). Please review and correct the rows below.`);
      }
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
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div>
                    <div style={{ fontWeight: 600, color: '#fff' }}>{asgn.course_name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Code: {asgn.course_code}</div>
                  </div>
                  <span className="badge badge-info">{asgn.session_name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upload Form */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.15rem' }}>📤 Submit Marks CSV</h3>
            <a
              href={api.getTemplateUrl()}
              download="marks_template.csv"
              className="btn btn-secondary btn-sm"
              target="_blank"
              rel="noreferrer"
            >
              📥 Download CSV Template
            </a>
          </div>

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
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.academic_year} - Sem {s.semester_number}) [{s.status}]
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Assigned Course</label>
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
              <label className="form-label">Total Maximum Marks for this Evaluation</label>
              <input
                type="number"
                className="form-input"
                min="1"
                max="1000"
                value={maxMarks}
                onChange={(e) => setMaxMarks(parseFloat(e.target.value) || 100)}
                required
              />
              <small style={{ color: 'var(--text-dim)', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                All marks submitted in this CSV will be validated against this maximum threshold.
              </small>
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
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.25rem' }}>Batch Review: {batchResult.file_name}</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Hash: <code style={{ fontFamily: 'var(--font-mono)' }}>{batchResult.file_hash.substring(0, 16)}...</code> | Max Marks: {batchResult.max_marks}
              </p>
            </div>
            <span className={`badge ${batchResult.status === 'PENDING_APPROVAL' ? 'badge-pass' : 'badge-fail'}`}>
              {batchResult.status}
            </span>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Registration #</th>
                  <th>Student Name</th>
                  <th>Marks Obtained</th>
                  <th>Absent?</th>
                  <th>Status</th>
                  <th>Validation Message</th>
                </tr>
              </thead>
              <tbody>
                {batchResult.rows && batchResult.rows.map((row: any) => (
                  <tr key={row.row_number}>
                    <td>{row.row_number}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.registration_number}</td>
                    <td>{row.student_name || '—'}</td>
                    <td>{row.is_absent ? <span style={{ color: 'var(--warning)' }}>AB</span> : row.marks_obtained}</td>
                    <td>{row.is_absent ? 'YES' : 'NO'}</td>
                    <td>
                      <span className={`badge ${row.is_valid ? 'badge-pass' : 'badge-fail'}`}>
                        {row.is_valid ? 'VALID' : 'INVALID'}
                      </span>
                    </td>
                    <td style={{ color: row.is_valid ? 'var(--text-muted)' : 'var(--danger)', fontSize: '0.85rem' }}>
                      {row.error_message || 'OK'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
