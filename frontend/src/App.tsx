import { useState, useEffect } from 'react';
import { api, type UserSession } from './api/client';
import { Navbar } from './components/Navbar';
import { LoginView } from './components/LoginView';
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
  };

  const handleLogout = () => {
    localStorage.removeItem('srp_token');
    setCurrentUser(null);
  };

  const handleQuickPersonaSwitch = async (role: 'ADMIN' | 'TEACHER' | 'STUDENT') => {
    let email = 'admin@institution.edu';
    let pass = 'AdminSecret123!';
    if (role === 'TEACHER') {
      email = 'teacher@institution.edu';
      pass = 'TeacherSecret123!';
    } else if (role === 'STUDENT') {
      email = 'student@institution.edu';
      pass = 'StudentSecret123!';
    }

    try {
      const session = await api.login(email, pass);
      localStorage.setItem('srp_token', session.token);
      setCurrentUser(session.user);
    } catch (err: any) {
      alert(`Could not switch to ${role}: ${err.message || 'Check database seed'}`);
    }
  };

  if (initializing) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🎓</div>
          <div style={{ color: 'var(--text-muted)' }}>Loading Student Result Portal...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Navbar
        user={currentUser}
        onLogout={handleLogout}
        onQuickLogin={handleQuickPersonaSwitch}
      />

      <main className="main-content">
        {!currentUser ? (
          <LoginView onLoginSuccess={handleLoginSuccess} />
        ) : currentUser.role === 'ADMIN' ? (
          <AdminDashboard />
        ) : currentUser.role === 'TEACHER' ? (
          <TeacherDashboard />
        ) : (
          <StudentDashboard />
        )}
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '2rem 1rem',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '0.8rem',
        color: 'var(--text-dim)',
      }}>
        Student Result Portal (SRP) &bull; Enterprise Monolith Architecture &bull; All Actions Audited
      </footer>
    </div>
  );
}

export default App;
