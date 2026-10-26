import React, { useState, useEffect } from 'react';
import { api, type UserSession } from '../api/client';

interface LoginViewProps {
  onLoginSuccess: (session: UserSession) => void;
  isEmbedded?: boolean;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess, isEmbedded = false }) => {
  const [isBootstrapMode, setIsBootstrapMode] = useState(false);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);

  // Form Fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    const checkSystem = async () => {
      try {
        const res = await api.getSetupStatus();
        if (res.needs_setup) {
          setNeedsSetup(true);
          setIsBootstrapMode(true);
        }
      } catch {
        // Fallback to standard login
      } finally {
        setCheckingSetup(false);
      }
    };
    checkSystem();
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const session = await api.login(email.trim(), password);
      localStorage.setItem('srp_token', session.token);
      onLoginSuccess(session);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleBootstrap = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must contain at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await api.bootstrapAdmin({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
      });
      setSuccessMsg('Administrator account registered. Authenticating...');
      const session = await api.login(email.trim(), password);
      localStorage.setItem('srp_token', session.token);
      onLoginSuccess(session);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize system administrator.');
    } finally {
      setLoading(false);
    }
  };

  if (checkingSetup) {
    return (
      <div style={{ maxWidth: '440px', margin: '48px auto', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p>Connecting to portal services...</p>
      </div>
    );
  }

  return (
    <div id="portal-access" style={{ maxWidth: '460px', margin: isEmbedded ? '0 auto' : '48px auto' }}>
      <div className="card" style={{ padding: '32px', textAlign: 'left' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-xl)',
              background: 'var(--primary-subtle)',
              color: 'var(--primary)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px'
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '6px' }}>
            {isBootstrapMode ? 'System setup: Administrator' : 'Portal authentication'}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            {isBootstrapMode
              ? 'Initialize the primary institution administrator profile.'
              : 'Enter institutional credentials to view or publish academic records.'}
          </p>
        </div>

        {needsSetup && (
          <div style={{
            padding: '12px',
            background: 'var(--info-bg)',
            border: '1px solid var(--info-border)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--info)',
            fontSize: '13px',
            marginBottom: '16px'
          }}>
            <strong>Clean installation detected:</strong> Please register your institution primary super administrator below.
          </div>
        )}

        {error && (
          <div style={{
            padding: '12px',
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--danger)',
            fontSize: '13px',
            marginBottom: '16px'
          }}>
            <strong>Authentication notice:</strong> {error}
          </div>
        )}

        {successMsg && (
          <div style={{
            padding: '12px',
            background: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--success)',
            fontSize: '13px',
            marginBottom: '16px'
          }}>
            {successMsg}
          </div>
        )}

        {isBootstrapMode ? (
          <form onSubmit={handleBootstrap}>
            <div className="form-group">
              <label className="form-label" htmlFor="setup-name">Full name and academic title</label>
              <input
                id="setup-name"
                type="text"
                className="form-input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Eleanor Vance, Dean"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="setup-email">Administrator email</label>
              <input
                id="setup-email"
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@institution.edu"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="setup-password">Master password</label>
              <input
                id="setup-password"
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="setup-confirm">Confirm master password</label>
              <input
                id="setup-confirm"
                type="password"
                className="form-input"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat password"
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '8px' }}
              disabled={loading}
            >
              {loading ? 'Initializing administrator...' : 'Create super administrator account'}
            </button>

            {!needsSetup && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                style={{ width: '100%', marginTop: '12px' }}
                onClick={() => { setIsBootstrapMode(false); setError(null); }}
              >
                Back to standard sign in
              </button>
            )}
          </form>
        ) : (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label" htmlFor="login-email">Institutional email address</label>
              <input
                id="login-email"
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@institution.edu"
                required
              />
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label" htmlFor="login-password">Password</label>
              </div>
              <input
                id="login-password"
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '8px' }}
              disabled={loading}
            >
              {loading ? 'Authenticating credentials...' : 'Sign in to portal'}
            </button>

            <div style={{ marginTop: '20px', textAlign: 'center', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                type="button"
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--primary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textDecoration: 'none'
                }}
                onClick={() => { setIsBootstrapMode(true); setError(null); }}
              >
                Initialize master administrator profile
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
