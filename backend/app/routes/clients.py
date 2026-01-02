from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db, require_admin
from app.schemas import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(
    response: Response,
    q: str | None = None,
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
            return crud.list_clients_including_archived(db, q=q)
        return crud.list_clients(db, q=q)

    current_page = page or 1
    current_page_size = page_size or 20
    offset = (current_page - 1) * current_page_size
    if include_archived:
        items, total = crud.list_clients_page_including_archived(db, q=q, offset=offset, limit=current_page_size)
    else:
        items, total = crud.list_clients_page(db, q=q, offset=offset, limit=current_page_size)

    total_pages = (total + current_page_size - 1) // current_page_size if current_page_size else 0
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(current_page)
    response.headers["X-Page-Size"] = str(current_page_size)
    response.headers["X-Total-Pages"] = str(total_pages)
    return items


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = crud.create_client(db, data=payload.model_dump())
    crud.create_audit_log(
        db,
        entity_type="client",
        entity_id=client.id,
        action="create",
        actor_user=current_user,
        summary=f"Created client: {client.name}",
    )
    return client


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    client = crud.get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = crud.get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    updated = crud.update_client(db, client=client, data=payload.model_dump())
    crud.create_audit_log(
        db,
        entity_type="client",
        entity_id=updated.id,
        action="update",
        actor_user=current_user,
        summary=f"Updated client: {updated.name}",
    )
    return updated


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    client = crud.get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    crud.delete_client(db, client=client)
    crud.create_audit_log(
        db,
        entity_type="client",
        entity_id=client.id,
        action="archive",
        actor_user=current_user,
        summary=f"Archived client: {client.name}",
    )
    return None


@router.post("/{client_id}/restore", response_model=ClientRead)
def restore_client(client_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    client = crud.get_client_including_archived(db, client_id=client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    restored = crud.restore_client(db, client=client)
    crud.create_audit_log(
        db,
        entity_type="client",
        entity_id=restored.id,
        action="restore",
        actor_user=current_user,
        summary=f"Restored client: {restored.name}",
    )
    return restored
