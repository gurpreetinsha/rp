import { useState, useEffect } from 'react';
import { api, type UserSession } from './api/client';
import { Navbar } from './components/Navbar';
import { LandingPage } from './components/LandingPage';
import { AdminDashboard } from './components/AdminDashboard';
import { TeacherDashboard } from './components/TeacherDashboard';
import { StudentDashboard } from './components/StudentDashboard';

export function App() {
  const [currentUser, setCurrentUser] = useState<UserSession['user'] | null>(null);
  const [initializing, setInitializing] = useState<boolean>(() => !!localStorage.getItem('srp_token'));

  useEffect(() => {
    const token = localStorage.getItem('srp_token');
    if (!token) {
      return;
    }
    api.getMe()
      .then((user) => setCurrentUser(user))
      .catch(() => {
        localStorage.removeItem('srp_token');
        setCurrentUser(null);
      })
      .finally(() => setInitializing(false));
  }, []);

  const handleLoginSuccess = (session: UserSession) => {
    setCurrentUser(session.user);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = () => {
    localStorage.removeItem('srp_token');
    setCurrentUser(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (initializing) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#ffffff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '40px', marginBottom: '16px' }}>🎓</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '15px', fontWeight: 600 }}>Loading Student Result Portal...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Navbar
        user={currentUser}
        onLogout={handleLogout}
      />

      <main className="main-content" id="main-content">
        {!currentUser ? (
          <LandingPage onLoginSuccess={handleLoginSuccess} />
        ) : (
          <div className="content-container" style={{ padding: '32px 24px' }}>
            {currentUser.role === 'ADMIN' ? (
              <AdminDashboard />
            ) : currentUser.role === 'TEACHER' ? (
              <TeacherDashboard />
            ) : (
              <StudentDashboard />
            )}
          </div>
        )}
      </main>

      {currentUser && (
        <footer style={{
          textAlign: 'center',
          padding: '32px 16px',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '13px',
          color: 'var(--text-dim)',
          backgroundColor: 'var(--bg-surface-elevated)'
        }}>
          Student Result Portal &bull; Enterprise Academic Architecture &bull; All Actions Audited
        </footer>
      )}
    </div>
  );
}

export default App;
