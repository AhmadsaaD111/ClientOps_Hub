from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.routes.auth import router as auth_router
from app.routes.audit_logs import router as audit_logs_router
from app.routes.clients import router as clients_router
from app.routes.invoices import router as invoices_router
from app.routes.leads import router as leads_router
from app.seed import seed_if_empty

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size", "X-Total-Pages"],
)


def _ensure_soft_delete_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as conn:
        for table in ["clients", "leads", "invoices"]:
            cols = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()]
            if "deleted_at" not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN deleted_at DATETIME"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                  id INTEGER PRIMARY KEY,
                  entity_type VARCHAR(50) NOT NULL,
                  entity_id INTEGER NOT NULL,
                  action VARCHAR(50) NOT NULL,
                  actor_user_id INTEGER NOT NULL,
                  actor_role VARCHAR(20) NOT NULL,
                  summary VARCHAR(255),
                  created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
                )
                """
            )
        )

        for idx in [
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs (entity_type)",
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs (entity_id)",
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action)",
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_user_id ON audit_logs (actor_user_id)",
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at)",
        ]:
            conn.execute(text(idx))


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _ensure_soft_delete_columns()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(audit_logs_router, prefix=settings.api_v1_prefix)
app.include_router(clients_router, prefix=settings.api_v1_prefix)
app.include_router(leads_router, prefix=settings.api_v1_prefix)
app.include_router(invoices_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
