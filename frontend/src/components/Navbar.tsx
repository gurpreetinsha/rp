import React from 'react';
import type { UserSession } from '../api/client';

interface NavbarProps {
  user: UserSession['user'] | null;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
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

        <div className="nav-links">
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
    </header>
  );
};
