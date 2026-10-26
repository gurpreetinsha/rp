import React, { useState, useEffect, useRef } from 'react';
import { LoginView } from './LoginView';
import { type UserSession } from '../api/client';

interface LandingPageProps {
  onLoginSuccess: (session: UserSession) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onLoginSuccess }) => {
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(0);
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);
  const [demoRegNumber, setDemoRegNumber] = useState<string>('REG2024001');
  const [verifiedResult, setVerifiedResult] = useState<{
    studentName: string;
    program: string;
    semester: number;
    gpa: string;
    cgpa: string;
    status: 'PASS' | 'DISTINCTION';
    credits: number;
    timestamp: string;
    hash: string;
  } | null>(null);

  // Tagline Reveal Section logic per B11:
  // Words transition individually from muted opacity to full text color in reading order on scroll.
  const taglineRef = useRef<HTMLDivElement>(null);
  const [revealedWordCount, setRevealedWordCount] = useState<number>(0);

  const taglineText = "Every student grade deserves complete auditability and instant verification without manual delays.";
  const taglineWords = taglineText.split(' ');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            let count = 0;
            const timer = setInterval(() => {
              count += 1;
              setRevealedWordCount(count);
              if (count >= taglineWords.length) {
                clearInterval(timer);
              }
            }, 60);
            observer.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );

    if (taglineRef.current) {
      observer.observe(taglineRef.current);
    }

    return () => observer.disconnect();
  }, [taglineWords.length]);

  // Scroll reveal observer for sections
  useEffect(() => {
    const reveals = document.querySelectorAll('.reveal-on-scroll');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );

    reveals.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const handleVerifyDemo = (e: React.FormEvent) => {
    e.preventDefault();
    if (!demoRegNumber.trim()) return;

    // Simulate instant cryptographic verification
    setVerifiedResult({
      studentName: demoRegNumber.toUpperCase() === 'REG2024002' ? 'Marcus Vance' : 'Sophia Montgomery',
      program: 'Bachelor of Science in Computer Science',
      semester: 6,
      gpa: demoRegNumber.toUpperCase() === 'REG2024002' ? '3.82' : '3.94',
      cgpa: demoRegNumber.toUpperCase() === 'REG2024002' ? '3.76' : '3.91',
      status: 'DISTINCTION',
      credits: 24,
      timestamp: '2026-10-24 14:32:08 UTC',
      hash: 'SHA256: 8f4b2c1e9a3d76e05c8b2a1f4e9d0c3a5b7e1f2a'
    });
  };

  const faqItems = [
    {
      question: "How does the portal prevent unauthorized grade adjustments after publication?",
      answer: "Every mark submission is cryptographically signed and stored in an immutable audit log. Once the examination board approves a session and publishes results, individual faculty permissions are locked, and any emergency correction requires dual administrator authorization with a logged rationale."
    },
    {
      question: "Can faculty members upload marks for multiple subjects at once?",
      answer: "Yes. Faculty members can upload standard spreadsheet files with automatic header mapping and syntax validation. The portal immediately checks for boundary values, missing entries, and credit weights before presenting a verification preview."
    },
    {
      question: "How are semester grade point averages and cumulative averages calculated?",
      answer: "The computation engine applies the university standard credit weighted scoring formula. Course grade points are multiplied by course credits, summed across the academic term, and divided by total registered credits in under 48 milliseconds."
    },
    {
      question: "What happens if a student has an administrative hold or withheld result?",
      answer: "Administrators can mark specific student records as withheld with an official reason note. The student receives a clear notice upon authentication, while public verification prevents disclosure until the administrative hold is resolved."
    },
    {
      question: "Can students download and print authentic paper marksheets?",
      answer: "Yes. Students and registrars can print official electronic statements of marks with standardized university seal watermarks, complete subject breakdowns, credit hours, and unique verification tokens designed specifically for academic transcripts."
    },
    {
      question: "How do colleges initialize the master administrator during setup?",
      answer: "Upon first deployment with a clean database, the portal presents an automated system setup view allowing the institution to designate the primary academic dean or registrar with master administrative privileges."
    }
  ];

  return (
    <div id="main-content">
      {/* 1. HERO SECTION */}
      <section id="overview" className="hero-section">
        <div className="content-container">
          <div className="hero-content">
            <h1 className="hero-heading">
              Publish verified academic results<br />with zero calculation errors
            </h1>

            <p className="hero-subheading">
              Universities and autonomous colleges replace fragile manual spreadsheets with an audited computation engine and instant marksheet generation.
            </p>

            <div className="hero-actions">
              <a
                href="#portal-access"
                className="btn btn-primary"
                onClick={(e) => {
                  e.preventDefault();
                  setShowLoginModal(true);
                }}
              >
                Access examination portal
              </a>
              <a href="#verification" className="btn btn-secondary">
                Verify student marksheet
              </a>
            </div>

            <div className="hero-proof">
              <div className="hero-proof-avatars" aria-hidden="true">
                <div className="hero-proof-avatar" style={{ backgroundColor: '#2563eb' }} />
                <div className="hero-proof-avatar" style={{ backgroundColor: '#0284c7' }} />
                <div className="hero-proof-avatar" style={{ backgroundColor: '#16a34a' }} />
              </div>
              <span>Trusted across 18 university departments with 142,850 verified grade records</span>
            </div>
          </div>

          {/* Hero Visual Preview */}
          <div className="hero-mock-container reveal-on-scroll">
            {/* Mock Window Header */}
            <div className="hero-mock-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ef4444', display: 'inline-block', flexShrink: 0 }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b', display: 'inline-block', flexShrink: 0 }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block', flexShrink: 0 }} />
                <span className="hero-mock-url">
                  srp.university.edu/records/verification/REG2024001
                </span>
              </div>
              <span className="badge badge-pass" style={{ fontSize: '11px', flexShrink: 0 }}>
                Board Approved
              </span>
            </div>

            {/* Mock Marksheet Content */}
            <div className="hero-mock-body">
              <div className="hero-mock-meta">
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--primary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
                    Official Academic Transcript
                  </div>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                    Spring 2026 Examination Session
                  </h3>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    Student: <strong>Sophia Montgomery</strong> &bull; Registration: <code style={{ fontFamily: 'var(--font-mono)' }}>REG2024001</code>
                  </div>
                </div>

                <div className="hero-mock-gpa-grid">
                  <div className="hero-mock-gpa-item">
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Semester GPA</div>
                    <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary)' }}>3.94</div>
                  </div>
                  <div className="hero-mock-gpa-item">
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Cumulative CGPA</div>
                    <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--success)' }}>3.91</div>
                  </div>
                </div>
              </div>

              {/* Course Grade Table Preview */}
              <div className="table-responsive" style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Course Code</th>
                      <th>Course Title</th>
                      <th>Credits</th>
                      <th>Marks (100)</th>
                      <th>Grade Point</th>
                      <th>Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>CS401</td>
                      <td>Advanced Distributed Systems</td>
                      <td>4</td>
                      <td>94</td>
                      <td>4.00</td>
                      <td><span className="badge badge-pass">Pass</span></td>
                    </tr>
                    <tr>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>CS408</td>
                      <td>Cryptographic Protocols</td>
                      <td>4</td>
                      <td>91</td>
                      <td>4.00</td>
                      <td><span className="badge badge-pass">Pass</span></td>
                    </tr>
                    <tr>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>MA302</td>
                      <td>Discrete Probability and Statistics</td>
                      <td>3</td>
                      <td>87</td>
                      <td>3.70</td>
                      <td><span className="badge badge-pass">Pass</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', fontSize: '12px', color: 'var(--text-dim)' }}>
                <span>Engine calculation latency: 38ms</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>Cryptographic token: SHA256: 8f4b...7e1f</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. TAGLINE REVEAL SECTION (MANDATORY B11) */}
      <section ref={taglineRef} className="tagline-section">
        <div className="tagline-container">
          <div className="tagline-label">Core academic principle</div>
          <p className="tagline-text">
            {taglineWords.map((word, idx) => (
              <span
                key={idx}
                className={`tagline-word ${idx < revealedWordCount ? 'revealed' : ''}`}
              >
                {word}
              </span>
            ))}
          </p>
        </div>
      </section>

      {/* 3. PROBLEM TO SOLUTION SECTION */}
      <section className="section-wrapper">
        <div className="content-container">
          <div className="section-header">
            <span className="section-tag">The operational challenge</span>
            <h2 className="section-title">Manual spreadsheet grading slows institutions down</h2>
            <p className="section-desc">
              When marks are compiled across detached spreadsheets, universities face recurring grading errors, unauthorized grade alterations, and multi week delays before students receive their official transcripts.
            </p>
          </div>

          <div
            className="reveal-on-scroll"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px',
              maxWidth: '960px',
              margin: '0 auto'
            }}
          >
            <div className="card" style={{ backgroundColor: 'var(--danger-bg)', borderColor: 'var(--danger-border)' }}>
              <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--danger)', marginBottom: '8px' }}>
                Without automated marks validation
              </div>
              <ul style={{ paddingLeft: '20px', color: 'var(--text-muted)', fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li>Rounding discrepancies across departments leading to student revaluation appeals</li>
                <li>No immutable logs tracking who edited a score or when a change occurred</li>
                <li>Paper marksheets vulnerable to physical alteration or forgery</li>
                <li>Weeks spent compiling aggregate statistics manually at semester close</li>
              </ul>
            </div>

            <div className="card" style={{ backgroundColor: 'var(--success-bg)', borderColor: 'var(--success-border)' }}>
              <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--success)', marginBottom: '8px' }}>
                With Student Result Portal
              </div>
              <ul style={{ paddingLeft: '20px', color: 'var(--text-muted)', fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li>Deterministic grading algorithms calculating GPA and CGPA in less than 48 milliseconds</li>
                <li>Every faculty score upload, edit, and board approval tracked with precise audit timestamps</li>
                <li>Cryptographic hashes on digital marksheets allowing instant employer verification</li>
                <li>Immediate publication to authenticated student portals upon committee approval</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 4. BENEFITS SECTION */}
      <section id="benefits" className="section-wrapper">
        <div className="content-container">
          <div className="section-header">
            <span className="section-tag">Key capabilities</span>
            <h2 className="section-title">Built for institutional rigor and student clarity</h2>
            <p className="section-desc">
              Engineered specifically for university examination divisions requiring exact computation and complete accountability.
            </p>
          </div>

          <div className="benefits-grid">
            <div className="benefit-card reveal-on-scroll">
              <div className="benefit-icon-box" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
                  <path d="M6 6h10"/>
                  <path d="M6 10h10"/>
                </svg>
              </div>
              <h3 className="benefit-title">Automated GPA calculation</h3>
              <p className="benefit-text">
                Computes semester and cumulative grades in 48 milliseconds with zero rounding discrepancies across complex credit structures.
              </p>
            </div>

            <div className="benefit-card reveal-on-scroll">
              <div className="benefit-icon-box" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
                  <path d="m9 12 2 2 4-4"/>
                </svg>
              </div>
              <h3 className="benefit-title">Complete audit trails</h3>
              <p className="benefit-text">
                Logs every faculty score submission, approval timestamp, and moderation event into an immutable examination ledger.
              </p>
            </div>

            <div className="benefit-card reveal-on-scroll">
              <div className="benefit-icon-box" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="2" y1="12" x2="22" y2="12"/>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
              </div>
              <h3 className="benefit-title">Instant student verification</h3>
              <p className="benefit-text">
                Provides secure digital marksheets with cryptographic hash verification for prospective employers and academic registrars.
              </p>
            </div>

            <div className="benefit-card reveal-on-scroll">
              <div className="benefit-icon-box" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect width="18" height="18" x="3" y="3" rx="2"/>
                  <path d="M3 9h18"/>
                  <path d="M9 21V9"/>
                </svg>
              </div>
              <h3 className="benefit-title">Role gated access controls</h3>
              <p className="benefit-text">
                Isolates administrator publishing from faculty marks entry to eliminate unauthorized adjustments and maintain integrity.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 5. HOW IT WORKS (3 CLEAR STEPS) */}
      <section id="how-it-works" className="section-wrapper">
        <div className="content-container">
          <div className="section-header">
            <span className="section-tag">Examination lifecycle</span>
            <h2 className="section-title">How examination records flow to publication</h2>
            <p className="section-desc">
              A structured three step process ensuring accuracy from individual classroom evaluation to university wide release.
            </p>
          </div>

          <div className="steps-grid">
            <div className="step-card reveal-on-scroll">
              <span className="step-number">Step 01</span>
              <h3 className="step-title">Faculty score submission</h3>
              <p className="step-text">
                Course instructors input marks through standardized templates with client validation ensuring scores stay within prescribed maximum ranges.
              </p>
            </div>

            <div className="step-card reveal-on-scroll">
              <span className="step-number">Step 02</span>
              <h3 className="step-title">Automated audit and computation</h3>
              <p className="step-text">
                The computation engine verifies credit multipliers, calculates letter grades, checks moderation criteria, and flags incomplete submissions.
              </p>
            </div>

            <div className="step-card reveal-on-scroll">
              <span className="step-number">Step 03</span>
              <h3 className="step-title">Board approval and release</h3>
              <p className="step-text">
                The examination controller reviews aggregate analytics, locks the session with an administrator digital key, and publishes marksheets instantly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. INTERACTIVE MARKSHEET VERIFICATION WIDGET */}
      <section id="verification" className="section-wrapper">
        <div className="content-container">
          <div className="section-header">
            <span className="section-tag">Public transcript verification</span>
            <h2 className="section-title">Verify student marksheet authenticity</h2>
            <p className="section-desc">
              Employers and higher education institutions can check any official credential instantly using a registration number.
            </p>
          </div>

          <div className="card verification-card reveal-on-scroll">
            <form onSubmit={handleVerifyDemo}>
              <div className="form-group">
                <label className="form-label" htmlFor="verification-input">
                  Enter student registration number
                </label>
                <div className="verification-form-row">
                  <input
                    id="verification-input"
                    type="text"
                    className="form-input"
                    value={demoRegNumber}
                    onChange={(e) => setDemoRegNumber(e.target.value)}
                    placeholder="e.g. REG2024001"
                    required
                  />
                  <button type="submit" className="btn btn-primary verification-submit-btn">
                    Verify marksheet
                  </button>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
                <span>Try sample registrations:</span>
                <button
                  type="button"
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer', padding: 0 }}
                  onClick={() => setDemoRegNumber('REG2024001')}
                >
                  REG2024001
                </button>
                <span>&bull;</span>
                <button
                  type="button"
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer', padding: 0 }}
                  onClick={() => setDemoRegNumber('REG2024002')}
                >
                  REG2024002
                </button>
              </div>
            </form>

            {verifiedResult && (
              <div
                style={{
                  marginTop: '24px',
                  padding: '20px',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-xl)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span className="badge badge-pass">Authentic verified record</span>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                    Verified {verifiedResult.timestamp}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '13px', marginBottom: '12px' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Student Name:</span>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{verifiedResult.studentName}</div>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Program of Study:</span>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{verifiedResult.program}</div>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Semester GPA:</span>
                    <div style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '16px' }}>{verifiedResult.gpa}</div>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Cumulative CGPA:</span>
                    <div style={{ fontWeight: 700, color: 'var(--success)', fontSize: '16px' }}>{verifiedResult.cgpa}</div>
                  </div>
                </div>

                <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                  {verifiedResult.hash}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 7. INSTITUTIONAL METRICS AND SOCIAL PROOF */}
      <section className="section-wrapper">
        <div className="content-container">
          <div className="metrics-grid reveal-on-scroll">
            <div className="stat-card">
              <div className="stat-label">Processed marks</div>
              <div className="stat-value">142,850+</div>
              <div className="stat-subtext">Across semester examination sessions</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Academic departments</div>
              <div className="stat-value">18</div>
              <div className="stat-subtext">Science, Engineering, and Humanities</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Calculation speed</div>
              <div className="stat-value">48ms</div>
              <div className="stat-subtext">Per entire cohort grade evaluation</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Portal uptime</div>
              <div className="stat-value">99.98%</div>
              <div className="stat-subtext">Audited academic year availability</div>
            </div>
          </div>

          {/* Testimonial Quote */}
          <div
            className="card reveal-on-scroll"
            style={{
              maxWidth: '760px',
              margin: '32px auto 0 auto',
              padding: '32px',
              textAlign: 'center'
            }}
          >
            <p style={{ fontSize: '18px', lineHeight: '28px', color: 'var(--text-main)', marginBottom: '16px' }}>
              "Switching from disconnected evaluation spreadsheets to the Student Result Portal reduced our post examination audit period from three weeks down to two days, with complete confidence in our published grades."
            </p>
            <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '15px' }}>
              Dr. Eleanor Vance
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Dean of Academic Affairs, Metropolitan Institute of Technology
            </div>
          </div>
        </div>
      </section>

      {/* 8. EMBEDDED PORTAL AUTHENTICATION SECTION */}
      <section className="section-wrapper" style={{ backgroundColor: 'var(--bg-surface-elevated)' }}>
        <div className="content-container">
          <div className="section-header">
            <span className="section-tag">Direct portal sign in</span>
            <h2 className="section-title">Access your academic account</h2>
            <p className="section-desc">
              Students view published marksheets. Faculty submit evaluation scores. Administrators manage institution sessions.
            </p>
          </div>

          <LoginView onLoginSuccess={onLoginSuccess} isEmbedded={true} />
        </div>
      </section>

      {/* 9. FAQ SECTION (6 QUESTIONS) */}
      <section id="faq" className="section-wrapper">
        <div className="content-container">
          <div className="section-header">
            <span className="section-tag">Common questions</span>
            <h2 className="section-title">Frequently asked questions</h2>
            <p className="section-desc">
              Clear answers regarding marksheet generation, calculation rules, and institution governance.
            </p>
          </div>

          <div className="faq-list">
            {faqItems.map((item, idx) => {
              const isOpen = openFaqIndex === idx;
              return (
                <div key={idx} className="faq-item reveal-on-scroll">
                  <button
                    type="button"
                    className="faq-question"
                    onClick={() => setOpenFaqIndex(isOpen ? null : idx)}
                    aria-expanded={isOpen}
                  >
                    <span>{item.question}</span>
                    <span className="faq-icon" style={{ transform: isOpen ? 'rotate(180deg)' : 'none' }}>
                      ↓
                    </span>
                  </button>
                  {isOpen && (
                    <div className="faq-answer">
                      <p>{item.answer}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 10. RISK REVERSAL & FINAL CTA */}
      <section className="section-wrapper" style={{ textAlign: 'center', padding: '80px 0' }}>
        <div className="content-container">
          <div style={{ maxWidth: '680px', margin: '0 auto' }}>
            <span className="section-tag">Academic integrity standard</span>
            <h2 className="section-title" style={{ marginBottom: '16px' }}>
              Publish verified results without delays
            </h2>
            <p className="section-desc" style={{ marginBottom: '32px' }}>
              Compliant with university grading standards, complete immutable audit trails, and zero data tampering guarantee.
            </p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowLoginModal(true)}
            >
              Access examination portal
            </button>
          </div>
        </div>
      </section>

      {/* 11. FOOTER WITH LEGAL LINKS & ACCESSIBILITY */}
      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-top">
            <div className="footer-brand">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '20px' }}>🎓</span>
                <span style={{ fontWeight: 700, fontSize: '16px', color: 'var(--text-main)' }}>
                  Student Result Portal
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Official electronic examination evaluation, calculation engine, and certified marksheet publication platform.
              </p>
            </div>

            <div className="footer-links-group">
              <div>
                <div className="footer-column-title">Portal Navigation</div>
                <ul className="footer-links-list">
                  <li><a href="#overview" className="footer-link">Overview</a></li>
                  <li><a href="#benefits" className="footer-link">System Benefits</a></li>
                  <li><a href="#how-it-works" className="footer-link">How It Works</a></li>
                  <li><a href="#verification" className="footer-link">Credential Verification</a></li>
                </ul>
              </div>

              <div>
                <div className="footer-column-title">Compliance and Policy</div>
                <ul className="footer-links-list">
                  <li><a href="#faq" className="footer-link">Privacy Policy</a></li>
                  <li><a href="#faq" className="footer-link">Terms of Service</a></li>
                  <li><a href="#faq" className="footer-link">FERPA Compliance</a></li>
                  <li><a href="#faq" className="footer-link">Audit Guidelines</a></li>
                </ul>
              </div>

              <div>
                <div className="footer-column-title">Institution Support</div>
                <ul className="footer-links-list">
                  <li><a href="#portal-access" className="footer-link">Administrator Setup</a></li>
                  <li><a href="#verification" className="footer-link">Transcript Registry</a></li>
                  <li><a href="mailto:support@university.edu" className="footer-link">Examination Desk</a></li>
                </ul>
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <div>
              Student Result Portal &bull; Enterprise Academic Architecture &bull; All Actions Audited
            </div>
            <div>
              Designed strictly under white theme specification &bull; Version 2.4.0
            </div>
          </div>
        </div>
      </footer>

      {/* QUICK LOGIN MODAL */}
      {showLoginModal && (
        <div className="modal-overlay" onClick={() => setShowLoginModal(false)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '480px', padding: 0 }}
          >
            <div className="modal-header">
              <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Portal Authentication</h3>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setShowLoginModal(false)}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>
            <div style={{ padding: '24px' }}>
              <LoginView
                onLoginSuccess={(session) => {
                  setShowLoginModal(false);
                  onLoginSuccess(session);
                }}
                isEmbedded={true}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
