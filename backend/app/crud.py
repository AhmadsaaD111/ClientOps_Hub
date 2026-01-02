from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.models import AuditLog, Client, Invoice, InvoiceStatus, Lead, User, UserRole


def get_user_by_username(db: Session, *, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, *, username: str, password: str, role: UserRole) -> User:
    user = User(username=username, hashed_password=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_audit_log(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    action: str,
    actor_user: User,
    summary: str | None = None,
) -> AuditLog:
    row = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_user_id=actor_user.id,
        actor_role=actor_user.role.value,
        summary=summary,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_audit_logs(db: Session) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    return list(db.scalars(stmt).all())


def list_audit_logs_page(db: Session, *, offset: int, limit: int) -> tuple[list[AuditLog], int]:
    total = int(db.scalar(select(func.count()).select_from(AuditLog)) or 0)
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    items = list(db.scalars(stmt).all())
    return items, total


def list_clients(db: Session, *, q: str | None = None) -> list[Client]:
    stmt = select(Client).where(Client.deleted_at.is_(None)).order_by(Client.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Client.name.ilike(like)) | (Client.company.ilike(like)))
    return list(db.scalars(stmt).all())


def list_clients_including_archived(db: Session, *, q: str | None = None) -> list[Client]:
    stmt = select(Client).order_by(Client.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Client.name.ilike(like)) | (Client.company.ilike(like)))
    return list(db.scalars(stmt).all())


def list_clients_page(
    db: Session,
    *,
    q: str | None = None,
    offset: int,
    limit: int,
) -> tuple[list[Client], int]:
    stmt = select(Client).where(Client.deleted_at.is_(None))
    count_stmt = select(func.count()).select_from(Client).where(Client.deleted_at.is_(None))

    if q:
        like = f"%{q.strip()}%"
        condition = (Client.name.ilike(like)) | (Client.company.ilike(like))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(stmt.order_by(Client.created_at.desc()).offset(offset).limit(limit)).all()
    )
    return items, total


def list_clients_page_including_archived(
    db: Session,
    *,
    q: str | None = None,
    offset: int,
    limit: int,
) -> tuple[list[Client], int]:
    stmt = select(Client)
    count_stmt = select(func.count()).select_from(Client)

    if q:
        like = f"%{q.strip()}%"
        condition = (Client.name.ilike(like)) | (Client.company.ilike(like))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    items = list(db.scalars(stmt.order_by(Client.created_at.desc()).offset(offset).limit(limit)).all())
    return items, total


def get_client(db: Session, *, client_id: int) -> Client | None:
    stmt = select(Client).where(Client.id == client_id, Client.deleted_at.is_(None))
    return db.scalar(stmt)


def get_client_including_archived(db: Session, *, client_id: int) -> Client | None:
    stmt = select(Client).where(Client.id == client_id)
    return db.scalar(stmt)


def create_client(db: Session, *, data: dict) -> Client:
    client = Client(**data)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, *, client: Client, data: dict) -> Client:
    for k, v in data.items():
        setattr(client, k, v)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, *, client: Client) -> None:
    now = datetime.now(timezone.utc)
    if client.deleted_at is None:
        client.deleted_at = now
        for inv in client.invoices:
            if inv.deleted_at is None:
                inv.deleted_at = now

    db.add(client)
    db.commit()


def restore_client(db: Session, *, client: Client) -> Client:
    client.deleted_at = None
    for inv in client.invoices:
        inv.deleted_at = None
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def list_leads(db: Session) -> list[Lead]:
    stmt = select(Lead).where(Lead.deleted_at.is_(None)).order_by(Lead.created_at.desc())
    return list(db.scalars(stmt).all())


def list_leads_including_archived(db: Session) -> list[Lead]:
    return list(db.scalars(select(Lead).order_by(Lead.created_at.desc())).all())


def list_leads_page(db: Session, *, offset: int, limit: int) -> tuple[list[Lead], int]:
    total = int(
        db.scalar(select(func.count()).select_from(Lead).where(Lead.deleted_at.is_(None))) or 0
    )
    items = list(
        db.scalars(
            select(Lead)
            .where(Lead.deleted_at.is_(None))
            .order_by(Lead.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )
    return items, total


def list_leads_page_including_archived(db: Session, *, offset: int, limit: int) -> tuple[list[Lead], int]:
    total = int(db.scalar(select(func.count()).select_from(Lead)) or 0)
    items = list(
        db.scalars(select(Lead).order_by(Lead.created_at.desc()).offset(offset).limit(limit)).all()
    )
    return items, total


def get_lead(db: Session, *, lead_id: int) -> Lead | None:
    stmt = select(Lead).where(Lead.id == lead_id, Lead.deleted_at.is_(None))
    return db.scalar(stmt)


def get_lead_including_archived(db: Session, *, lead_id: int) -> Lead | None:
    stmt = select(Lead).where(Lead.id == lead_id)
    return db.scalar(stmt)


def create_lead(db: Session, *, data: dict) -> Lead:
    lead = Lead(**data)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def update_lead(db: Session, *, lead: Lead, data: dict) -> Lead:
    for k, v in data.items():
        setattr(lead, k, v)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def delete_lead(db: Session, *, lead: Lead) -> None:
    if lead.deleted_at is None:
        lead.deleted_at = datetime.now(timezone.utc)
        db.add(lead)
        db.commit()


def restore_lead(db: Session, *, lead: Lead) -> Lead:
    lead.deleted_at = None
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def list_invoices(db: Session) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .join(Invoice.client)
        .where(Invoice.deleted_at.is_(None), Client.deleted_at.is_(None))
        .options(selectinload(Invoice.client))
        .order_by(Invoice.issued_at.desc())
    )
    return list(db.scalars(stmt).all())


def list_invoices_including_archived(db: Session) -> list[Invoice]:
    stmt = select(Invoice).options(selectinload(Invoice.client)).order_by(Invoice.issued_at.desc())
    return list(db.scalars(stmt).all())


def list_invoices_page(db: Session, *, offset: int, limit: int) -> tuple[list[Invoice], int]:
    total = int(
        db.scalar(
            select(func.count())
            .select_from(Invoice)
            .join(Invoice.client)
            .where(Invoice.deleted_at.is_(None), Client.deleted_at.is_(None))
        )
        or 0
    )
    stmt = (
        select(Invoice)
        .join(Invoice.client)
        .where(Invoice.deleted_at.is_(None), Client.deleted_at.is_(None))
        .options(selectinload(Invoice.client))
        .order_by(Invoice.issued_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(stmt).all())
    return items, total


def list_invoices_page_including_archived(
    db: Session, *, offset: int, limit: int
) -> tuple[list[Invoice], int]:
    total = int(db.scalar(select(func.count()).select_from(Invoice)) or 0)
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.client))
        .order_by(Invoice.issued_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(stmt).all())
    return items, total


def get_invoice(db: Session, *, invoice_id: int) -> Invoice | None:
    stmt = (
        select(Invoice)
        .join(Invoice.client)
        .where(Invoice.id == invoice_id, Invoice.deleted_at.is_(None), Client.deleted_at.is_(None))
        .options(selectinload(Invoice.client))
    )
    return db.scalar(stmt)


def get_invoice_including_archived(db: Session, *, invoice_id: int) -> Invoice | None:
    stmt = select(Invoice).options(selectinload(Invoice.client)).where(Invoice.id == invoice_id)
    return db.scalar(stmt)


def create_invoice(db: Session, *, data: dict) -> Invoice:
    invoice = Invoice(**data)
    if invoice.status == InvoiceStatus.paid and invoice.paid_at is None:
        invoice.paid_at = datetime.now(timezone.utc)
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def update_invoice(db: Session, *, invoice: Invoice, data: dict) -> Invoice:
    for k, v in data.items():
        setattr(invoice, k, v)

    if invoice.status == InvoiceStatus.paid and invoice.paid_at is None:
        invoice.paid_at = datetime.now(timezone.utc)
    if invoice.status != InvoiceStatus.paid:
        invoice.paid_at = None

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice(db: Session, *, invoice: Invoice) -> None:
    if invoice.deleted_at is None:
        invoice.deleted_at = datetime.now(timezone.utc)
        db.add(invoice)
        db.commit()


def restore_invoice(db: Session, *, invoice: Invoice) -> Invoice:
    invoice.deleted_at = None
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
