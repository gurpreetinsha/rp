import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'sessions' | 'imports' | 'calculate_publish' | 'amendments' | 'audit'>('calculate_publish');

  // Core Data
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');

  // Calculation & Summary State
  const [summary, setSummary] = useState<any | null>(null);
  const [sessionResults, setSessionResults] = useState<any[]>([]);
  const [officialMarks, setOfficialMarks] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Modals & Action States
  const [loading, setLoading] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<{ text: string; type: 'success' | 'danger' } | null>(null);

  // Amendment modal
  const [selectedMarkForAmend, setSelectedMarkForAmend] = useState<any | null>(null);
  const [amendMarks, setAmendMarks] = useState<number>(0);
  const [amendAbsent, setAmendAbsent] = useState<boolean>(false);
  const [amendReason, setAmendReason] = useState<string>('');
  const [amendmentHistory, setAmendmentHistory] = useState<any[]>([]);

  // Withhold modal
  const [withholdTarget, setWithholdTarget] = useState<any | null>(null);
  const [withholdReason, setWithholdReason] = useState<string>('');

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (selectedSessionId) {
      loadSessionData(selectedSessionId);
    }
  }, [selectedSessionId, activeTab]);

  const loadSessions = async () => {
    try {
      const sess = await api.getSessions();
      setSessions(sess);
      if (sess.length > 0 && !selectedSessionId) {
        setSelectedSessionId(sess[0].id);
      }
    } catch (err: any) {
      showMessage(err.message || 'Failed to load initial academic data.', 'danger');
    }
  };

  const loadSessionData = async (sessId: string) => {
    setLoading(true);
    try {
      if (activeTab === 'calculate_publish') {
        const [sum, res] = await Promise.allSettled([
          api.getSessionSummary(sessId),
          api.listSessionResults(sessId),
        ]);
        if (sum.status === 'fulfilled') setSummary(sum.value);
        else setSummary(null);

        if (res.status === 'fulfilled') setSessionResults(res.value);
        else setSessionResults([]);
      } else if (activeTab === 'amendments' || activeTab === 'imports') {
        const marks = await api.getOfficialMarks(sessId);
        setOfficialMarks(marks);
      } else if (activeTab === 'audit') {
        const logs = await api.getAuditLogs(100);
        setAuditLogs(logs);
      }
    } catch (err: any) {
      // Non-blocking
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (text: string, type: 'success' | 'danger') => {
    setActionMsg({ text, type });
    setTimeout(() => setActionMsg(null), 5000);
  };

  // 1. Session Status Change
  const handleStatusChange = async (newStatus: string) => {
    if (!selectedSessionId) return;
    try {
      await api.updateSessionStatus(selectedSessionId, newStatus);
      showMessage(`Session status transitioned to ${newStatus}`, 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to update session status', 'danger');
    }
  };

  // 2. Calculation
  const handleCalculate = async (allowPartial: boolean = false) => {
    if (!selectedSessionId) return;
    setLoading(true);
    try {
      const sum = await api.calculateResults(selectedSessionId, allowPartial);
      setSummary(sum);
      showMessage('Academic evaluation completed successfully!', 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Calculation failed.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 3. Publication
  const handlePublish = async () => {
    if (!selectedSessionId) return;
    setLoading(true);
    try {
      const sum = await api.publishSession(selectedSessionId);
      setSummary(sum);
      showMessage('Results published officially! Students can now access their electronic marksheets.', 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Publication failed.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 4. Unpublish Rollback
  const handleUnpublish = async () => {
    const reason = prompt('Please provide administrative reason for unpublishing:');
    if (!reason) return;
    setLoading(true);
    try {
      await api.unpublishSession(selectedSessionId, reason);
      showMessage('Session unpublished and rolled back to CALCULATED status.', 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to unpublish session.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 5. Withhold Toggle
  const handleToggleWithhold = async () => {
    if (!withholdTarget) return;
    try {
      await api.withholdResult(withholdTarget.id, !withholdTarget.is_withheld, withholdReason);
      showMessage(`Student result ${!withholdTarget.is_withheld ? 'withheld' : 'released'} successfully.`, 'success');
      setWithholdTarget(null);
      setWithholdReason('');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Withhold operation failed.', 'danger');
    }
  };

  // 6. Open Amendment Modal
  const openAmendmentModal = async (mark: any) => {
    setSelectedMarkForAmend(mark);
    setAmendMarks(mark.marks_obtained);
    setAmendAbsent(mark.is_absent);
    setAmendReason('');
    try {
      const history = await api.getMarkAmendments(mark.id);
      setAmendmentHistory(history);
    } catch {
      setAmendmentHistory([]);
    }
  };

  // 7. Submit Amendment
  const handleSubmitAmendment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMarkForAmend) return;
    if (!amendReason.trim()) {
      alert('A formal justification reason is strictly required for mark amendments.');
      return;
    }

    try {
      await api.amendOfficialMark(selectedMarkForAmend.id, {
        new_marks_obtained: amendMarks,
        new_is_absent: amendAbsent,
        reason: amendReason,
      });
      showMessage('Official mark amended successfully. Calculated results automatically synchronized!', 'success');
      setSelectedMarkForAmend(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Mark amendment failed.', 'danger');
    }
  };

  const currentSessionObj = sessions.find((s) => s.id === selectedSessionId);

  return (
    <div>
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>University Administration Control Deck</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Supervise evaluation sessions, review submitted marks batches, execute the calculation engine, and manage official result publications.
          </p>
        </div>

        {/* Global Session Selector */}
        <div style={{ minWidth: '280px' }}>
          <label className="form-label">Active Examination Session</label>
          <select
            className="form-select"
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.academic_year}) &bull; [{s.status}]
              </option>
            ))}
          </select>
        </div>
      </div>

      {actionMsg && (
        <div style={{
          padding: '1rem',
          background: actionMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
          border: `1px solid ${actionMsg.type === 'success' ? 'var(--success-border)' : 'var(--danger-border)'}`,
          borderRadius: 'var(--radius-md)',
          color: actionMsg.type === 'success' ? 'var(--success)' : 'var(--danger)',
          marginBottom: '1.5rem',
        }}>
          {actionMsg.type === 'success' ? '✅' : '⚠️'} {actionMsg.text}
        </div>
      )}

      {/* Tabs */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === 'calculate_publish' ? 'active' : ''}`}
          onClick={() => setActiveTab('calculate_publish')}
        >
          ⚡ Calculation & Publication
        </button>
        <button
          className={`tab-btn ${activeTab === 'amendments' ? 'active' : ''}`}
          onClick={() => setActiveTab('amendments')}
        >
          📝 Official Marks & Amendments
        </button>
        <button
          className={`tab-btn ${activeTab === 'sessions' ? 'active' : ''}`}
          onClick={() => setActiveTab('sessions')}
        >
          🏛️ Session Lifecycle
        </button>
        <button
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          🔒 Compliance Audit Trail
        </button>
      </div>

      {/* TAB 1: CALCULATION & PUBLICATION */}
      {activeTab === 'calculate_publish' && (
        <div>
          {/* Action Header Card */}
          <div className="glass-panel" style={{ marginBottom: '1.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                CURRENT SESSION STATUS
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.25rem' }}>
                <span className="badge badge-info" style={{ fontSize: '1rem', padding: '0.4rem 1rem' }}>
                  {currentSessionObj?.status || 'UNKNOWN'}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  Term: {currentSessionObj?.academic_year} &bull; Semester {currentSessionObj?.semester_number}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                className="btn btn-primary"
                onClick={() => handleCalculate(false)}
                disabled={loading || currentSessionObj?.status === 'PUBLISHED'}
              >
                ⚙️ Run Calculation Engine
              </button>

              {currentSessionObj?.status === 'CALCULATED' && (
                <button
                  className="btn btn-success"
                  onClick={handlePublish}
                  disabled={loading}
                >
                  🚀 Publish Official Results
                </button>
              )}

              {currentSessionObj?.status === 'PUBLISHED' && (
                <button
                  className="btn btn-danger btn-sm"
                  onClick={handleUnpublish}
                  disabled={loading}
                >
                  ↩️ Rollback (Unpublish)
                </button>
              )}
            </div>
          </div>

          {/* Metrics Overview */}
          {summary && (
            <div className="metrics-grid">
              <div className="stat-card">
                <div className="stat-label">Students Evaluated</div>
                <div className="stat-value">{summary.total_students_evaluated}</div>
                <div className="stat-subtext">Out of {summary.total_students_enrolled} enrolled</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Overall Pass Rate</div>
                <div className="stat-value" style={{ color: 'var(--success)' }}>
                  {summary.overall_pass_percentage.toFixed(1)}%
                </div>
                <div className="stat-subtext">{summary.total_passed} Passed &bull; {summary.total_failed} Failed</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Top Performance</div>
                <div className="stat-value" style={{ color: 'var(--accent-cyan)' }}>
                  {summary.highest_percentage.toFixed(1)}%
                </div>
                <div className="stat-subtext">Class Average: {summary.average_percentage.toFixed(1)}%</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Withheld Records</div>
                <div className="stat-value" style={{ color: summary.total_withheld > 0 ? 'var(--warning)' : '#fff' }}>
                  {summary.total_withheld}
                </div>
                <div className="stat-subtext">Masked from student portal</div>
              </div>
            </div>
          )}

          {/* Student Results List */}
          <div className="glass-panel">
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>🎓 Evaluated Student Results Roster</h3>
            {sessionResults.length === 0 ? (
              <p style={{ color: 'var(--text-dim)' }}>No calculated results found. Click "Run Calculation Engine" above.</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Reg Number</th>
                      <th>Student Name</th>
                      <th>Program</th>
                      <th>Total Obtained</th>
                      <th>Max Marks</th>
                      <th>Percentage</th>
                      <th>Result Status</th>
                      <th>Withheld?</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessionResults.map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{r.registration_number}</td>
                        <td style={{ fontWeight: 500 }}>{r.student_name}</td>
                        <td>{r.program_code}</td>
                        <td>{r.total_marks_obtained.toFixed(1)}</td>
                        <td>{r.total_max_marks.toFixed(1)}</td>
                        <td style={{ fontWeight: 700 }}>{r.percentage.toFixed(2)}%</td>
                        <td>
                          <span className={`badge ${r.result_status === 'PASS' ? 'badge-pass' : 'badge-fail'}`}>
                            {r.result_status}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${r.is_withheld ? 'badge-warning' : 'badge-pass'}`}>
                            {r.is_withheld ? 'WITHHELD' : 'RELEASED'}
                          </span>
                        </td>
                        <td>
                          <button
                            className={`btn ${r.is_withheld ? 'btn-success' : 'btn-secondary'} btn-sm`}
                            onClick={() => {
                              setWithholdTarget(r);
                              setWithholdReason('');
                            }}
                          >
                            {r.is_withheld ? 'Release' : 'Withhold'}
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
      )}

      {/* TAB 2: OFFICIAL MARKS & AMENDMENTS */}
      {activeTab === 'amendments' && (
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.25rem' }}>Official Approved Marks Registry</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                All approved academic marks for this session. Use the "Amend Mark" tool to perform auditable post-publication corrections.
              </p>
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reg Number</th>
                  <th>Student Name</th>
                  <th>Course</th>
                  <th>Marks Obtained</th>
                  <th>Max Marks</th>
                  <th>%</th>
                  <th>Absent?</th>
                  <th>Amended?</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {officialMarks.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{m.registration_number}</td>
                    <td>{m.student_name}</td>
                    <td><strong style={{ color: 'var(--accent-cyan)' }}>{m.course_code}</strong> - {m.course_name}</td>
                    <td style={{ fontWeight: 700 }}>{m.is_absent ? 'AB' : m.marks_obtained}</td>
                    <td>{m.max_marks}</td>
                    <td>{m.percentage.toFixed(2)}%</td>
                    <td>{m.is_absent ? 'YES' : 'NO'}</td>
                    <td>
                      {m.is_amended ? (
                        <span className="badge badge-warning">AMENDED</span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>ORIGINAL</span>
                      )}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => openAmendmentModal(m)}
                      >
                        ✏️ Amend Mark
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: SESSION LIFECYCLE */}
      {activeTab === 'sessions' && (
        <div className="glass-panel">
          <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Academic Session Workflow State Machine</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Regulate the active phase of this examination session. Transitions enforce academic integrity constraints.
          </p>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary"
              onClick={() => handleStatusChange('MARKS_ENTRY_OPEN')}
              disabled={currentSessionObj?.status === 'MARKS_ENTRY_OPEN'}
            >
              🔓 Open Marks Entry
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => handleStatusChange('MARKS_LOCKED')}
              disabled={currentSessionObj?.status === 'MARKS_LOCKED'}
            >
              🔒 Lock Marks Entry
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => handleStatusChange('ARCHIVED')}
              disabled={currentSessionObj?.status === 'ARCHIVED'}
            >
              📦 Archive Session
            </button>
          </div>
        </div>
      )}

      {/* TAB 4: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="glass-panel">
          <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>🔒 Immutable Compliance Audit Log</h3>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>User</th>
                  <th>Entity Type</th>
                  <th>Entity ID</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td><span className="badge badge-info">{log.action}</span></td>
                    <td style={{ fontWeight: 600 }}>{log.user_name}</td>
                    <td style={{ color: 'var(--accent-cyan)' }}>{log.entity_type}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{log.entity_id.substring(0, 8)}...</td>
                    <td style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {log.details ? JSON.stringify(log.details) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: POST-PUBLICATION AMENDMENT */}
      {selectedMarkForAmend && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Amend Official Mark: {selectedMarkForAmend.student_name}</h3>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedMarkForAmend(null)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmitAmendment}>
              <div className="modal-body">
                <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
                  <div>Registration: <strong>{selectedMarkForAmend.registration_number}</strong></div>
                  <div>Course: <strong>{selectedMarkForAmend.course_code} - {selectedMarkForAmend.course_name}</strong></div>
                  <div>Current Official Mark: <strong>{selectedMarkForAmend.marks_obtained} / {selectedMarkForAmend.max_marks}</strong></div>
                </div>

                <div className="form-group">
                  <label className="form-label">New Marks Obtained (Max: {selectedMarkForAmend.max_marks})</label>
                  <input
                    type="number"
                    step="0.5"
                    className="form-input"
                    value={amendMarks}
                    disabled={amendAbsent}
                    onChange={(e) => setAmendMarks(parseFloat(e.target.value) || 0)}
                    required={!amendAbsent}
                  />
                </div>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={amendAbsent}
                      onChange={(e) => setAmendAbsent(e.target.checked)}
                    />
                    Mark Student as Absent (AB)
                  </label>
                </div>

                <div className="form-group">
                  <label className="form-label">Mandatory Correction Justification / Academic Senate Reason</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    value={amendReason}
                    onChange={(e) => setAmendReason(e.target.value)}
                    placeholder="e.g. Scrutiny committee re-evaluation, revised after verification."
                    required
                  />
                </div>

                {amendmentHistory.length > 0 && (
                  <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
                    <h5 style={{ marginBottom: '0.5rem' }}>Previous Amendments History</h5>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {amendmentHistory.map((h) => (
                        <div key={h.id} style={{ marginBottom: '0.5rem', padding: '0.5rem', background: 'var(--bg-surface-elevated)', borderRadius: '4px' }}>
                          Changed from <strong>{h.old_marks_obtained}</strong> to <strong>{h.new_marks_obtained}</strong> on {new Date(h.amended_at).toLocaleString()}: <em>"{h.reason}"</em>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setSelectedMarkForAmend(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirm & Sync Results
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: WITHHOLD CONFIRMATION */}
      {withholdTarget && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>{withholdTarget.is_withheld ? 'Release Result' : 'Withhold Result'}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setWithholdTarget(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ marginBottom: '1rem' }}>
                Are you sure you want to <strong>{withholdTarget.is_withheld ? 'release' : 'withhold'}</strong> the examination result for <strong>{withholdTarget.student_name}</strong> ({withholdTarget.registration_number})?
              </p>
              <div className="form-group">
                <label className="form-label">Reason / Administrative Notice</label>
                <input
                  type="text"
                  className="form-input"
                  value={withholdReason}
                  onChange={(e) => setWithholdReason(e.target.value)}
                  placeholder="e.g. Pending tuition clearance / Academic inquiry"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setWithholdTarget(null)}>Cancel</button>
              <button
                className={`btn ${withholdTarget.is_withheld ? 'btn-success' : 'btn-danger'}`}
                onClick={handleToggleWithhold}
              >
                Confirm {withholdTarget.is_withheld ? 'Release' : 'Withhold'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
