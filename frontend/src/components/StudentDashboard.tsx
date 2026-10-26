import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

export const StudentDashboard: React.FC = () => {
  const [marksheets, setMarksheets] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await api.getMyResults();
      setMarksheets(results);
      if (results.length > 0) {
        setSelectedSessionId((prev) => prev || results[0].session_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load official examination marksheets.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadResults();
  }, [loadResults]);

  const currentSheet = marksheets.find((m) => m.session_id === selectedSessionId) || marksheets[0];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.4rem' }}>Student Academic Records</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Official electronic statement of grades and evaluation outcomes issued by the University Examination Branch.
          </p>
        </div>
        {marksheets.length > 0 && !currentSheet?.is_withheld && (
          <button className="btn btn-secondary" onClick={() => window.print()}>
            🖨️ Print Marksheet
          </button>
        )}
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

      {loading ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>⏳</div>
          <p style={{ color: 'var(--text-muted)' }}>Fetching official published marksheets...</p>
        </div>
      ) : marksheets.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📜</div>
          <h3 style={{ fontSize: '1.4rem', marginBottom: '0.5rem' }}>No Published Results Yet</h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: '540px', margin: '0 auto' }}>
            There are currently no officially published examination results released for your student profile.
            Results will appear here automatically once the academic committee approves and publishes the session.
          </p>
        </div>
      ) : (
        <div>
          {/* Session Switcher if multiple published sessions */}
          {marksheets.length > 1 && (
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', overflowX: 'auto' }}>
              {marksheets.map((sheet) => (
                <button
                  key={sheet.session_id}
                  className={`btn ${sheet.session_id === selectedSessionId ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                  onClick={() => setSelectedSessionId(sheet.session_id)}
                >
                  {sheet.session_name} (Sem {sheet.semester_number})
                </button>
              ))}
            </div>
          )}

          {/* If Result is Withheld */}
          {currentSheet.is_withheld ? (
            <div className="glass-panel" style={{ border: '2px solid var(--warning-border)', textAlign: 'center', padding: '3rem 2rem' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
              <h2 style={{ color: 'var(--warning)', marginBottom: '0.75rem' }}>Result Status: WITHHELD</h2>
              <p style={{ color: 'var(--text-main)', fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto 1.5rem auto' }}>
                {currentSheet.notice || 'Your official result for this examination session has been temporarily withheld.'}
              </p>
              <div style={{
                display: 'inline-block',
                background: 'var(--bg-surface-elevated)',
                padding: '0.75rem 1.5rem',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-muted)',
                fontSize: '0.85rem'
              }}>
                Registration No: <strong style={{ color: 'var(--text-main)' }}>{currentSheet.registration_number}</strong> | Session: <strong style={{ color: 'var(--text-main)' }}>{currentSheet.session_name}</strong>
              </div>
            </div>
          ) : (
            /* Official Published Marksheet Card */
            <div className="marksheet-card">
              <div className="marksheet-header">
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginBottom: '0.35rem' }}>
                    University Examination Board
                  </div>
                  <h2 style={{ fontSize: '1.65rem', marginBottom: '0.25rem' }}>{currentSheet.session_name}</h2>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Academic Term: {currentSheet.academic_year} &bull; Semester {currentSheet.semester_number}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.35rem' }}>RESULT STATUS</div>
                  <span className={`badge ${currentSheet.result_status === 'PASS' ? 'badge-pass' : 'badge-fail'}`} style={{ fontSize: '0.95rem', padding: '0.4rem 1rem' }}>
                    {currentSheet.result_status}
                  </span>
                </div>
              </div>

              {/* Student Metadata Row */}
              <div className="marksheet-meta-grid">
                <div>
                  <div className="stat-label">Student Name</div>
                  <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-main)' }}>{currentSheet.student_name}</div>
                </div>
                <div>
                  <div className="stat-label">Registration Number</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '1rem', color: 'var(--text-main)' }}>
                    {currentSheet.registration_number}
                  </div>
                </div>
                <div>
                  <div className="stat-label">Academic Program</div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)' }}>
                    {currentSheet.program_name} ({currentSheet.program_code})
                  </div>
                </div>
                <div>
                  <div className="stat-label">Overall Percentage</div>
                  <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.35rem', fontWeight: 800, color: currentSheet.result_status === 'PASS' ? 'var(--success)' : 'var(--danger)' }}>
                    {currentSheet.percentage?.toFixed(2)}%
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    {currentSheet.total_marks_obtained} / {currentSheet.total_max_marks} Total
                  </div>
                </div>
              </div>

              {/* Subject Breakdown Table */}
              <div className="table-responsive" style={{ border: 'none', borderRadius: 0 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Course Code</th>
                      <th>Course Title</th>
                      <th>Credits</th>
                      <th>Marks Obtained</th>
                      <th>Max Marks</th>
                      <th>Percentage</th>
                      <th>Status</th>
                      <th>Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentSheet.subjects && currentSheet.subjects.map((sub: any) => (
                      <tr key={sub.course_code}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                          {sub.course_code}
                        </td>
                        <td style={{ fontWeight: 500 }}>{sub.course_name}</td>
                        <td>{sub.credits.toFixed(1)}</td>
                        <td style={{ fontWeight: 700 }}>
                          {sub.is_absent ? (
                            <span style={{ color: 'var(--warning)' }}>ABSENT (0.0)</span>
                          ) : (
                            sub.marks_obtained.toFixed(1)
                          )}
                        </td>
                        <td>{sub.max_marks.toFixed(1)}</td>
                        <td style={{ fontWeight: 600 }}>
                          {sub.is_absent ? '0.00%' : `${sub.percentage.toFixed(2)}%`}
                        </td>
                        <td>
                          <span className={`badge ${sub.is_passed ? 'badge-pass' : 'badge-fail'}`}>
                            {sub.is_passed ? 'PASS' : 'FAIL'}
                          </span>
                        </td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                          {sub.remarks || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Security & Verification Footer */}
              <div style={{
                padding: '1.25rem 2rem',
                background: 'var(--bg-surface-elevated)',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.75rem',
                color: 'var(--text-dim)'
              }}>
                <div>
                  🔒 Digitally verified academic record. Released: {currentSheet.published_at ? new Date(currentSheet.published_at).toLocaleString() : 'Official'}
                </div>
                <div>University Examination Division &bull; Confidential</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
