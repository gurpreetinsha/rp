import React, { useState, useEffect } from 'react';
import { api, API_BASE, type UserSession } from '../api/client';

interface NavbarProps {
  user: UserSession['user'] | null;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
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
    // Periodic light probe every 60s
    const timer = setInterval(testConnection, 60000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="brand">
          <div className="brand-icon">🎓</div>
          <div>
            <div>Student Result Portal</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}>
              Official Academic Marks & Results System
            </div>
          </div>
        </div>

        <div className="nav-links" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* Connection Status Pill */}
          <button
            type="button"
            onClick={() => setShowDiagModal(true)}
            style={{
              background: 'var(--bg-surface-elevated)',
              border: `1px solid ${healthStatus === 'connected' ? 'rgba(74, 222, 128, 0.4)' : healthStatus === 'checking' ? 'rgba(250, 204, 21, 0.4)' : 'rgba(248, 113, 113, 0.4)'}`,
              borderRadius: '20px',
              padding: '0.35rem 0.75rem',
              color: 'var(--text-main)',
              fontSize: '0.75rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              cursor: 'pointer',
            }}
            title="Click to view connection diagnostics"
          >
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: healthStatus === 'connected' ? '#4ade80' : healthStatus === 'checking' ? '#facc15' : '#f87171',
              display: 'inline-block',
              boxShadow: healthStatus === 'connected' ? '0 0 8px #4ade80' : 'none'
            }} />
            <span>
              {healthStatus === 'connected'
                ? `Online (${diagData?.latency || 0}ms)`
                : healthStatus === 'checking'
                ? 'Connecting...'
                : 'Connection Issue'}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>⚙️</span>
          </button>

          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#fff' }}>{user.full_name}</div>
                <span className={`badge ${user.role === 'ADMIN' ? 'badge-pass' : user.role === 'TEACHER' ? 'badge-info' : 'badge-warning'}`}>
                  {user.role}
                </span>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={onLogout}>
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>

      {/* DIAGNOSTICS MODAL */}
      {showDiagModal && (
        <div className="modal-overlay" style={{ zIndex: 9999 }}>
          <div className="modal-content" style={{ maxWidth: '560px' }}>
            <div className="modal-header">
              <h3>🔍 System Connection & Deployment Diagnostics</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowDiagModal(false)}>✕</button>
            </div>
            <div className="modal-body" style={{ fontSize: '0.9rem' }}>
              <div style={{ marginBottom: '1.25rem', padding: '0.75rem 1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Frontend URL (Vercel):</span>
                  <code style={{ fontSize: '0.8rem' }}>{window.location.origin}</code>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>API Target Prefix:</span>
                  <code style={{ fontSize: '0.8rem' }}>{API_BASE}</code>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Backend Service Status:</span>
                  <span style={{ fontWeight: 600, color: healthStatus === 'connected' ? 'var(--success)' : 'var(--danger)' }}>
                    {healthStatus === 'connected' ? '🟢 Reachable (200 OK)' : '🔴 Unreachable'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Database Connection:</span>
                  <span style={{ fontWeight: 600, color: diagData?.data?.database === 'connected' ? 'var(--success)' : 'var(--danger)' }}>
                    {diagData?.data?.database === 'connected' ? '🟢 Connected' : '🔴 Disconnected'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>API Roundtrip Latency:</span>
                  <span>{diagData?.latency ? `${diagData.latency} ms` : '—'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Environment Mode:</span>
                  <span className="badge badge-info">{diagData?.data?.environment || 'unknown'}</span>
                </div>
              </div>

              {diagData?.error && (
                <div style={{ padding: '0.75rem 1rem', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', borderRadius: 'var(--radius-md)', color: 'var(--danger)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  ⚠️ <strong>Diagnostic Error:</strong> {diagData.error}
                </div>
              )}

              <div style={{ background: 'rgba(56, 189, 248, 0.05)', border: '1px solid rgba(56, 189, 248, 0.2)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <div style={{ fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '0.25rem' }}>💡 Connection Checklist:</div>
                <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                  <li><strong>Render Free Tier:</strong> If backend was inactive, Render puts free containers to sleep. Waking up takes ~50s on the first request.</li>
                  <li><strong>Vercel Rewrites:</strong> Ensure requests to <code>/api/:path*</code> are proxied to <code>https://srpbackend.onrender.com/api/:path*</code>.</li>
                  <li><strong>Direct Backend URL:</strong> You can set <code>VITE_API_BASE_URL=https://srpbackend.onrender.com/api/v1</code> in Vercel environment variables to bypass rewrites.</li>
                </ul>
              </div>
            </div>
            <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={testConnection}
                disabled={testing}
              >
                {testing ? 'Testing Connection...' : '🔄 Test Connection Now'}
              </button>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowDiagModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
