# ClientOps Hub

ClientOps Hub is a small internal workspace for managing clients, leads, and invoices with an auditable change history. It’s designed for teams that want a clear operational view without adopting a full enterprise CRM.

## Features

- **Authentication**
  - JWT-based login
  - Role-based access (`admin`, `staff`)
- **Clients**
  - Create, update, search
  - Archive/restore (soft delete)
- **Leads**
  - Pipeline status tracking (`new`, `contacted`, `qualified`, `lost`)
  - Archive/restore (soft delete)
- **Invoices**
  - Linked to clients
  - Lifecycle status (`draft`, `sent`, `paid`)
  - Archive/restore (soft delete)
- **Audit log**
  - Records write actions: `create`, `update`, `archive`, `restore`, `status_change`
  - Admin-only endpoint and UI
- **Pagination**
  - Optional server-side paging for list endpoints with response headers for totals and page metadata

## Tech stack

- **Backend**
  - FastAPI
  - SQLAlchemy
  - Pydantic
  - SQLite (local persistence)
- **Frontend**
  - Vue 3
  - TypeScript
  - Pinia
  - Vue Router
  - Axios

## Architecture

The repository is split into two independent applications:

- `backend/`: REST API, persistence, authentication/authorization, auditing
- `frontend/`: SPA UI, session management, routing, API client

## Security & access control

- The API uses JWT bearer tokens (`Authorization: Bearer <token>`).
- Authorization is enforced server-side.
- `admin`-only operations include:
  - Viewing archived records (`include_archived=true`)
  - Restoring archived records
  - Audit log access

## Data and auditing guarantees

- **Soft delete**
  - Clients, leads, and invoices are archived via `deleted_at`.
  - List endpoints return active records by default.
  - Archived records can be requested by admins with `include_archived=true`.
  - Archiving a client also archives that client’s invoices.
- **Audit log**
  - Write operations create entries in `audit_logs` including actor, role, action, and timestamp.
  - Admin-only endpoint: `GET /api/audit-logs?page=1&page_size=20`

## Local development

### Backend

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
\.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

3. Create `backend/.env`:

- Copy from `backend/.env.example`
- Set a `SECRET_KEY` appropriate for your environment

4. Start the API:

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

The default SQLite database file is stored at `backend/clientops.db`.

API resources:

- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### Frontend

1. Install dependencies:

```powershell
npm --prefix frontend install
```

2. Create `frontend/.env`:

- Copy from `frontend/.env.example`

3. Start the dev server:

```powershell
npm --prefix frontend run dev
```

UI: `http://localhost:5173`

## Configuration

- Backend configuration is read from `backend/.env`.
- Frontend configuration is read from `frontend/.env`.

## Repository layout

```
backend/   # FastAPI application
frontend/  # Vue application
```

## Initial accounts

When the database is empty, the backend creates two accounts on startup:

- **Admin**: `admin` / `admin123`
- **Staff**: `staff` / `staff123`

## Maintenance & contribution

- Keep API behavior backward compatible where practical.
- Prefer small, focused changes.
- Include reproduction steps and environment details in issues.
- Run the backend and frontend locally before opening a pull request.
