from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db, require_admin
from app.schemas import InvoiceCreate, InvoiceReadWithClient, InvoiceUpdate

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceReadWithClient])
def list_invoices(
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
            return crud.list_invoices_including_archived(db)
        return crud.list_invoices(db)

    current_page = page or 1
    current_page_size = page_size or 20
    offset = (current_page - 1) * current_page_size
    if include_archived:
        items, total = crud.list_invoices_page_including_archived(db, offset=offset, limit=current_page_size)
    else:
        items, total = crud.list_invoices_page(db, offset=offset, limit=current_page_size)

    total_pages = (total + current_page_size - 1) // current_page_size if current_page_size else 0
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(current_page)
    response.headers["X-Page-Size"] = str(current_page_size)
    response.headers["X-Total-Pages"] = str(total_pages)
    return items


@router.post("", response_model=InvoiceReadWithClient, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = crud.get_client(db, client_id=payload.client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    invoice = crud.create_invoice(db, data=payload.model_dump())
    hydrated = crud.get_invoice(db, invoice_id=invoice.id)
    result = hydrated or invoice
    crud.create_audit_log(
        db,
        entity_type="invoice",
        entity_id=result.id,
        action="create",
        actor_user=current_user,
        summary=f"Created invoice: {result.title}",
    )
    return result


@router.get("/{invoice_id}", response_model=InvoiceReadWithClient)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceReadWithClient)
def update_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

    prev_status = invoice.status

    client = crud.get_client(db, client_id=payload.client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    updated = crud.update_invoice(db, invoice=invoice, data=payload.model_dump())
    hydrated = crud.get_invoice(db, invoice_id=updated.id)
    result = hydrated or updated
    action = "status_change" if payload.status != prev_status else "update"
    summary = (
        f"Invoice status: {result.title} {prev_status.value} → {result.status.value}"
        if action == "status_change"
        else f"Updated invoice: {result.title}"
    )
    crud.create_audit_log(
        db,
        entity_type="invoice",
        entity_id=result.id,
        action=action,
        actor_user=current_user,
        summary=summary,
    )
    return result


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    crud.delete_invoice(db, invoice=invoice)
    crud.create_audit_log(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="archive",
        actor_user=current_user,
        summary=f"Archived invoice: {invoice.title}",
    )
    return None


@router.post("/{invoice_id}/restore", response_model=InvoiceReadWithClient)
def restore_invoice(invoice_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    invoice = crud.get_invoice_including_archived(db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    restored = crud.restore_invoice(db, invoice=invoice)
    hydrated = crud.get_invoice_including_archived(db, invoice_id=restored.id)
    result = hydrated or restored
    crud.create_audit_log(
        db,
        entity_type="invoice",
        entity_id=result.id,
        action="restore",
        actor_user=current_user,
        summary=f"Restored invoice: {result.title}",
    )
    return result
