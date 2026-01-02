from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db, require_admin
from app.schemas import LeadCreate, LeadRead, LeadUpdate

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadRead])
def list_leads(
    response: Response,
    include_archived: bool = Query(default=False),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if include_archived and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges are required for this action.")

    if page is None and page_size is None:
        if include_archived:
            return crud.list_leads_including_archived(db)
        return crud.list_leads(db)

    current_page = page or 1
    current_page_size = page_size or 20
    offset = (current_page - 1) * current_page_size
    if include_archived:
        items, total = crud.list_leads_page_including_archived(db, offset=offset, limit=current_page_size)
    else:
        items, total = crud.list_leads_page(db, offset=offset, limit=current_page_size)

    total_pages = (total + current_page_size - 1) // current_page_size if current_page_size else 0
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(current_page)
    response.headers["X-Page-Size"] = str(current_page_size)
    response.headers["X-Total-Pages"] = str(total_pages)
    return items


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = crud.create_lead(db, data=payload.model_dump())
    crud.create_audit_log(
        db,
        entity_type="lead",
        entity_id=lead.id,
        action="create",
        actor_user=current_user,
        summary=f"Created lead: {lead.name}",
    )
    return lead


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    lead = crud.get_lead(db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    return lead


@router.put("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = crud.get_lead(db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    prev_status = lead.status
    updated = crud.update_lead(db, lead=lead, data=payload.model_dump())
    action = "status_change" if payload.status != prev_status else "update"
    summary = (
        f"Lead status: {updated.name} {prev_status.value} → {updated.status.value}"
        if action == "status_change"
        else f"Updated lead: {updated.name}"
    )
    crud.create_audit_log(
        db,
        entity_type="lead",
        entity_id=updated.id,
        action=action,
        actor_user=current_user,
        summary=summary,
    )
    return updated


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = crud.get_lead(db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    crud.delete_lead(db, lead=lead)
    crud.create_audit_log(
        db,
        entity_type="lead",
        entity_id=lead.id,
        action="archive",
        actor_user=current_user,
        summary=f"Archived lead: {lead.name}",
    )
    return None


@router.post("/{lead_id}/restore", response_model=LeadRead)
def restore_lead(lead_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    lead = crud.get_lead_including_archived(db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    restored = crud.restore_lead(db, lead=lead)
    crud.create_audit_log(
        db,
        entity_type="lead",
        entity_id=restored.id,
        action="restore",
        actor_user=current_user,
        summary=f"Restored lead: {restored.name}",
    )
    return restored
