import React, { useState, useEffect } from 'react';
import { api, API_BASE, type UserSession } from '../api/client';

interface NavbarProps {
  user: UserSession['user'] | null;
  onLogout: () => void;
  onOpenLogin?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout, onOpenLogin }) => {
  const [showDiagModal, setShowDiagModal] = useState(false);
  const [healthStatus, setHealthStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [diagData, setDiagData] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const testConnection = async () => {
    setTesting(true);
    setHealthStatus('checking');
    try {
      const result = await api.checkHealth();
      setDiagData(result);
      if (result.ok && result.data?.database === 'connected') {
        setHealthStatus('connected');
      } else {
        setHealthStatus('error');
      }
    } catch (err: any) {
      setDiagData({ ok: false, error: err.message || 'Network error' });
      setHealthStatus('error');
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    testConnection();
    const timer = setInterval(testConnection, 60000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="floating-navbar-wrapper">
      <header className="navbar">
        <div className="navbar-inner">
          <a href="#" className="brand" aria-label="Student Result Portal homepage">
            <div className="brand-icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                <path d="M6 12v5c3 3 9 3 12 0v-5"/>
              </svg>
            </div>
            <div>
              <div className="brand-title">Student Result Portal</div>
              <div className="brand-subtitle">Academic marks and publication system</div>
            </div>
          </a>

          {!user && (
            <nav className="nav-menu-links" aria-label="Main navigation">
              <a href="#overview" className="nav-link-item">Overview</a>
              <a href="#benefits" className="nav-link-item">Benefits</a>
              <a href="#how-it-works" className="nav-link-item">How it works</a>
              <a href="#verification" className="nav-link-item">Verification</a>
              <a href="#faq" className="nav-link-item">FAQ</a>
            </nav>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* System Status Pill */}
            <button
              type="button"
              onClick={() => setShowDiagModal(true)}
              className="btn btn-secondary btn-sm"
              style={{
                borderRadius: '9999px',
                padding: '4px 10px',
                fontSize: '12px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px'
              }}
              title="Click to view connection diagnostics"
            >
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: healthStatus === 'connected' ? '#16a34a' : healthStatus === 'checking' ? '#d97706' : '#dc2626',
                  display: 'inline-block'
                }}
              />
              <span>
                {healthStatus === 'connected'
                  ? `Online (${diagData?.latency || 0}ms)`
                  : healthStatus === 'checking'
                  ? 'Connecting...'
                  : 'Connection issue'}
              </span>
            </button>

            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-main)' }}>{user.full_name}</div>
                  <span className={`badge ${user.role === 'ADMIN' ? 'badge-pass' : user.role === 'TEACHER' ? 'badge-info' : 'badge-warning'}`}>
                    {user.role}
                  </span>
                </div>
                <button type="button" className="btn btn-secondary btn-sm" onClick={onLogout}>
                  Sign out
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => {
                  if (onOpenLogin) {
                    onOpenLogin();
                  } else {
                    const el = document.getElementById('portal-access');
                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
              >
                Access portal
              </button>
            )}
          </div>
        </div>

        {/* Diagnostics Modal */}
        {showDiagModal && (
          <div className="modal-overlay" onClick={() => setShowDiagModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Connection diagnostics</h3>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setShowDiagModal(false)}
                  aria-label="Close modal"
                >
                  ✕
                </button>
              </div>
              <div className="modal-body">
                <div style={{ marginBottom: '16px', padding: '12px 16px', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-lg)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Frontend URL:</span>
                    <code style={{ fontFamily: 'var(--font-mono)' }}>{window.location.origin}</code>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>API Target Prefix:</span>
                    <code style={{ fontFamily: 'var(--font-mono)' }}>{API_BASE}</code>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Backend Service Status:</span>
                    <span style={{ fontWeight: 600, color: healthStatus === 'connected' ? 'var(--success)' : 'var(--danger)' }}>
                      {healthStatus === 'connected' ? 'Reachable (200 OK)' : 'Unreachable'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Database Connection:</span>
                    <span style={{ fontWeight: 600, color: diagData?.data?.database === 'connected' ? 'var(--success)' : 'var(--danger)' }}>
                      {diagData?.data?.database === 'connected' ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Roundtrip Latency:</span>
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{diagData?.latency ? `${diagData.latency} ms` : '—'}</span>
                  </div>
                </div>

                {diagData?.error && (
                  <div style={{ padding: '12px', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', borderRadius: 'var(--radius-md)', color: 'var(--danger)', marginBottom: '16px', fontSize: '13px' }}>
                    <strong>Diagnostic note:</strong> {diagData.error}
                  </div>
                )}

                <div style={{ background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-subtle)', padding: '12px 16px', borderRadius: 'var(--radius-lg)', fontSize: '13px', color: 'var(--text-muted)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>Deployment guidelines:</div>
                  <ul style={{ paddingLeft: '18px', margin: 0, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <li>Render Free Tier puts inactive backend instances to sleep. Cold wake takes approximately 45 seconds on initial request.</li>
                    <li>Ensure API requests to <code>/api</code> are routed cleanly to the active backend instance.</li>
                  </ul>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={testConnection}
                  disabled={testing}
                >
                  {testing ? 'Testing connection...' : 'Test connection now'}
                </button>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowDiagModal(false)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </header>
    </div>
  );
};
