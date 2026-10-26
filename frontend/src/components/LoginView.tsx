import React, { useState, useEffect } from 'react';
import { api, type UserSession } from '../api/client';

interface LoginViewProps {
  onLoginSuccess: (session: UserSession) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
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
      const session = await api.login(email, password);
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
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);
    try {
      await api.bootstrapAdmin({
        email,
        password,
        full_name: fullName,
      });
      setSuccessMsg('Administrator account registered! Authenticating...');
      // Automatically log in
      const session = await api.login(email, password);
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
      <div style={{ maxWidth: '480px', margin: '4rem auto', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p>Connecting to portal services...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '480px', margin: '3rem auto' }}>
      <div className="glass-panel" style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>🏛️</div>
        <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
          {isBootstrapMode ? 'System Setup: Administrator' : 'Welcome to SRP'}
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.75rem' }}>
          {isBootstrapMode
            ? 'Initialize the primary institution administrator account for your portal.'
            : 'Official university examination marks evaluation, calculation, and result publication portal.'}
        </p>

        {needsSetup && (
          <div style={{
            padding: '0.75rem 1rem',
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--accent-cyan)',
            fontSize: '0.85rem',
            marginBottom: '1.25rem',
            textAlign: 'left'
          }}>
            ℹ️ <strong>Clean Installation Detected:</strong> Please register your institution's primary Super-Administrator below.
          </div>
        )}

        {error && (
          <div style={{
            padding: '0.75rem 1rem',
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--danger)',
            fontSize: '0.85rem',
            marginBottom: '1.25rem',
            textAlign: 'left'
          }}>
            ⚠️ {error}
          </div>
        )}

        {successMsg && (
          <div style={{
            padding: '0.75rem 1rem',
            background: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--success)',
            fontSize: '0.85rem',
            marginBottom: '1.25rem',
            textAlign: 'left'
          }}>
            ✅ {successMsg}
          </div>
        )}

        {isBootstrapMode ? (
          <form onSubmit={handleBootstrap} style={{ textAlign: 'left' }}>
            <div className="form-group">
              <label className="form-label">Full Name & Title</label>
              <input
                type="text"
                className="form-input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Dr. Jane Doe, Registrar"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Official Administrator Email</label>
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. admin@your-institution.edu"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Master Password</label>
              <input
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Master Password</label>
              <input
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
              style={{ width: '100%', padding: '0.8rem', marginTop: '0.5rem' }}
              disabled={loading}
            >
              {loading ? 'Initializing Administrator...' : 'Create Super-Administrator Account'}
            </button>

            {!needsSetup && (
              <button
                type="button"
                className="btn btn-secondary"
                style={{ width: '100%', marginTop: '0.75rem' }}
                onClick={() => { setIsBootstrapMode(false); setError(null); }}
              >
                Back to Standard Login
              </button>
            )}
          </form>
        ) : (
          <form onSubmit={handleLogin} style={{ textAlign: 'left' }}>
            <div className="form-group">
              <label className="form-label">Academic Email Address</label>
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. user@institution.edu"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
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
              style={{ width: '100%', padding: '0.8rem', marginTop: '0.5rem' }}
              disabled={loading}
            >
              {loading ? 'Authenticating...' : 'Sign In to Portal'}
            </button>

            <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
              <button
                type="button"
                style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => { setIsBootstrapMode(true); setError(null); }}
              >
                Need to initialize initial Super-Admin? Click here
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
