# Student Result Portal (SRP)

A robust, audited, and secure Student Result Portal designed for colleges and universities to manage the end-to-end examination result lifecycle: teacher mark submission via CSV, multi-tiered data validation, administrative approval, result calculation, and gated publication for students.

---

## Key Principles & Architectural Boundaries

1. **Separation of Concerns:**
   - **CSV Staging $\neq$ Official Marks:** Uploading marks validates and stages rows; it never directly creates official records.
   - **Validation $\neq$ Approval:** 100% valid batches require explicit administrative sign-off.
   - **Official Marks $\neq$ Calculated Results:** Results are calculated strictly according to approved academic rules.
   - **Calculations $\neq$ Published Results:** Results remain invisible to students until published by an authorized administrator.
2. **Modular Monolith:**
   - Single unified application with strict domain module separation (`auth`, `academic`, `users_mgmt`, `imports`, `marks`, `results`, `audit`).
3. **Auditability & Non-repudiation:**
   - Immutable audit logs record all critical administrative actions (approvals, rejections, imports, calculations, publications, amendments).

---

## Technology Stack

- **Operating System:** Windows 10
- **Backend:** Python 3.14+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Database:** PostgreSQL (with `psycopg` v3 driver)
- **Frontend:** React, TypeScript, Vite, Vanilla CSS
- **Testing:** `pytest` (backend), `vitest` (frontend)
- **Version Control:** Git

---

## Project Structure

```
rp/
├── .gitignore
├── .env.example
├── README.md
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── alembic.ini           # Alembic configuration
│   ├── app/
│   │   ├── core/             # Security, config, audit logging, exceptions
│   │   ├── database.py       # SQLAlchemy engine & session dependency
│   │   ├── main.py           # FastAPI entrypoint & router aggregation
│   │   └── modules/          # Domain-driven feature modules
│   ├── requirements.txt      # Python dependencies
│   └── tests/                # Automated pytest test suites
└── frontend/                 # React + TypeScript + Vite frontend
```

---

## Local Setup Instructions (Windows 10)

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js (v18+) and npm
- PostgreSQL 14+ installed and running locally

### 2. Backend Setup
1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd c:\Users\gurpr\18oc\rp\backend
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Copy `.env.example` to `.env`:
     ```powershell
     Copy-Item ..\.env.example .env
     ```
   - Edit `.env` to match your local PostgreSQL credentials and database name (`srp_db`).
5. Run database migrations:
   ```powershell
   alembic upgrade head
   ```
6. Start the FastAPI development server:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   Interactive API documentation will be available at `http://127.0.0.1:8000/docs`.

### 3. Running Backend Tests
```powershell
cd c:\Users\gurpr\18oc\rp\backend
.\.venv\Scripts\Activate.ps1
pytest -v
```

---

## Current Status & Implementation Stages
- **Stage 1: Project foundation** (Current)
- Stage 2: Database and academic setup
- Stage 3: Authentication and permissions
- Stage 4: Student and teacher management
- Stage 5: CSV upload and validation
- Stage 6: Import approval
- Stage 7: Result calculation
- Stage 8: Result publication
- Stage 9: Frontend
- Stage 10: Corrections, auditing, and security review
- Stage 11: Final testing and deployment preparation
