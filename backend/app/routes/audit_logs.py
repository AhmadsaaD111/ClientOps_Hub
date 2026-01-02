from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_db, require_admin
from app.schemas import AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    response: Response,
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if page is None and page_size is None:
        return crud.list_audit_logs(db)

    current_page = page or 1
    current_page_size = page_size or 20
    offset = (current_page - 1) * current_page_size
    items, total = crud.list_audit_logs_page(db, offset=offset, limit=current_page_size)

    total_pages = (total + current_page_size - 1) // current_page_size if current_page_size else 0
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(current_page)
    response.headers["X-Page-Size"] = str(current_page_size)
    response.headers["X-Total-Pages"] = str(total_pages)
    return items
