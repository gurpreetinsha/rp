# Student Result Portal (SRP)

A robust, audited, enterprise-grade Student Result Portal designed for colleges and universities to manage the end-to-end examination result lifecycle: faculty mark submission via CSV, multi-tiered data validation, administrative approval, dynamic calculation engine, post-publication amendments, and gated publication for students.

---

## 🏛️ Key Principles & Architectural Boundaries

1. **Separation of Concerns:**
   - **CSV Staging $\neq$ Official Marks:** Uploading marks validates and stages rows (`mark_import_batches`); it never directly creates official records.
   - **Validation $\neq$ Approval:** 100% valid batches require explicit administrative sign-off before committing to `official_marks`.
   - **Official Marks $\neq$ Calculated Results:** Results are calculated strictly according to approved academic rules (`calculated_results` and `result_subject_details`).
   - **Calculations $\neq$ Published Results:** Results remain strictly invisible to students until published by an authorized administrator.
2. **Academic Evaluation Rules:**
   - Single marks component (`marks_obtained`) validated against faculty-declared maximum marks (`max_marks`).
   - Absentee policy: `"AB"` / `is_absent = True` records 0 marks and marks subject as failed.
   - Result evaluation is **percentage only**: `(total_obtained / total_max) * 100`.
   - Course pass percentage threshold (e.g. 40.0%). Any subject failure leads to overall `FAIL`.
   - Withholding: Administrators can withhold individual student results (with mandatory justification), completely masking grades from student view while showing an official inquiry notice.
3. **Post-Publication Amendments & Auditability:**
   - Immutable audit logs (`audit_logs`) record all critical actions.
   - Post-publication corrections generate auditable `mark_amendments` records and dynamically synchronize calculated student results.

---

## 🛠️ Technology Stack

- **Operating System:** Windows 10
- **Backend:** Python 3.14+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Database:** PostgreSQL (with `psycopg` v3 binary driver) / SQLite for instant local development
- **Frontend:** React 19, TypeScript, Vite, Vanilla CSS (Tailored Design System)
- **Testing:** `pytest` (48 automated unit & integration tests)
- **Version Control:** Git

---

## 📁 Project Structure

```
rp/
├── backend/
│   ├── alembic/              # Database migration versions
│   ├── alembic.ini           # Alembic configuration
│   ├── app/
│   │   ├── core/             # Security, config, audit logging, exceptions
│   │   ├── database.py       # SQLAlchemy engine & session dependency
│   │   ├── main.py           # FastAPI entrypoint & router aggregation
│   │   ├── seed.py           # Realistic database seed script
│   │   └── modules/
│   │       ├── academic/     # Departments, programs, courses, sessions
│   │       ├── auth/         # Bcrypt, JWT tokens, RBAC dependencies
│   │       ├── users_mgmt/   # Students, teachers, assignments, enrollments
│   │       ├── imports/      # CSV template, 12-step validator, batch approval
│   │       ├── marks/        # Official marks registry & post-pub amendments
│   │       ├── results/      # Calculation engine, summaries, marksheets, withhold
│   │       └── audit/        # Immutable compliance audit log queries
│   ├── requirements.txt      # Python dependencies
│   └── tests/                # 48 Automated unit & integration tests
├── frontend/
│   ├── src/
│   │   ├── api/client.ts     # Centralized TypeScript API client
│   │   ├── components/
│   │   │   ├── Navbar.tsx    # Header with demo persona switcher
│   │   │   ├── LoginView.tsx # Authentication with 1-click presets
│   │   │   ├── AdminDashboard.tsx   # Admin control deck
│   │   │   ├── TeacherDashboard.tsx # Faculty CSV upload & validation
│   │   │   └── StudentDashboard.tsx # Published electronic marksheet
│   │   ├── index.css         # High-performance Vanilla CSS design system
│   │   ├── App.tsx           # App routing & persona state
│   │   └── main.tsx          # React DOM entrypoint
│   ├── package.json
│   └── vite.config.ts        # Vite dev server & API proxy
└── README.md
```

---

## 🚀 Quickstart Guide (Windows 10)

### 1. Database Seeding & Setup
Run the seed script to initialize the database with departments, courses, published marksheets, and demo accounts:
```powershell
$env:PYTHONPATH="backend"; .\backend\.venv\Scripts\python.exe -m app.seed
```

### 2. Preconfigured Demo Accounts
| Role | Email | Password | Details |
|---|---|---|---|
| **Admin** | `admin@institution.edu` | `AdminSecret123!` | Full control deck: calculations, publications, withhold, amendments, audit logs |
| **Teacher** | `teacher@institution.edu` | `TeacherSecret123!` | Faculty marks upload via CSV with live validation |
| **Student** | `student@institution.edu` | `StudentSecret123!` | Alice Smith (Reg: `STU-2026-001`, Passed with 88.33%) |
| **Student (Withheld)** | `student2@institution.edu` | `StudentSecret123!` | Bob Jones (Reg: `STU-2026-002`, Result Withheld) |
| **Student (Failed)** | `student3@institution.edu` | `StudentSecret123!` | Charlie Brown (Reg: `STU-2026-003`, Absent in CS302) |

---

### 3. Running the Backend Server
```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```
- API Docs (Swagger): `http://127.0.0.1:8000/docs`
- Health Probe: `http://127.0.0.1:8000/health`

---

### 4. Running the Frontend Development Server
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser. Use the header "Demo Switcher" buttons to easily switch between Admin, Teacher, and Student roles with a single click.

---

### 5. Running the Backend Automated Test Suite
```powershell
.\backend\.venv\Scripts\python.exe -m pytest .\backend\tests -v
```
All **48 automated unit and integration tests** pass cleanly with 100% coverage across:
- `test_health.py` (Liveness, readiness, OpenAPI docs)
- `test_academic.py` (Departments, programs, courses, sessions)
- `test_auth.py` (Bcrypt, JWT tokens, RBAC roles)
- `test_users_mgmt.py` (Students, teachers, enrollments, assignments)
- `test_csv_validation.py` (12-step validation engine, all-or-nothing staging)
- `test_import_approval.py` (Transactional approval, official marks, rejection)
- `test_calculations.py` (Engine evaluation, percentage math, absentee policy)
- `test_publication.py` (Publishing, student marksheet view, withholding masks)
- `test_amendments_and_audit.py` (Post-publication corrections, result sync, audit logs)

---

## 📋 Implementation Stages Completed
- [x] **Stage 1: Project foundation** (Git, config, exception architecture, virtualenv)
- [x] **Stage 2: Database and academic setup** (SQLAlchemy models, Alembic, academic REST APIs)
- [x] **Stage 3: Authentication and permissions** (Bcrypt, PyJWT, role-based access control)
- [x] **Stage 4: Student and teacher management** (User profiles, course assignments, enrollments)
- [x] **Stage 5: CSV upload and validation** (12-step validation engine, CSV template, batch staging)
- [x] **Stage 6: Import approval** (Batch approval to official marks, batch rejection, audit logs)
- [x] **Stage 7: Result calculation** (Evaluation engine, percentage calculation, absentee policy, metrics)
- [x] **Stage 8: Result publication** (Admin publication, student electronic marksheet, withholding masks)
- [x] **Stage 9: Frontend** (React + TypeScript + Vite, modern Vanilla CSS design system)
- [x] **Stage 10: Corrections & auditing** (Post-publication amendments, dynamic result sync, compliance logs)
- [x] **Stage 11: Final integration & verification** (Complete test suite: 48/48 tests passing, database seed)
