from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import create_client, create_invoice, create_lead, create_user
from app.models import InvoiceStatus, LeadStatus, User, UserRole

def seed_if_empty(db: Session) -> None:
    # Users
    has_users = db.scalar(select(User.id).limit(1)) is not None
    if not has_users:
        create_user(db, username="admin", password="admin123", role=UserRole.admin)
        create_user(db, username="staff", password="staff123", role=UserRole.staff)

    # Clients
    from app.models import Client, Invoice, Lead

    has_clients = db.scalar(select(Client.id).limit(1)) is not None
    if not has_clients:
        acme = create_client(
            db,
            data={
                "name": "Amina El-Sayed",
                "email": "amina@acme-consulting.com",
                "company": "ACME Consulting",
                "phone": "+20 100 000 0000",
                "notes": "Retainer client (monthly ops support).",
            },
        )
        northwind = create_client(
            db,
            data={
                "name": "Omar Hassan",
                "email": "omar@northwind-trading.com",
                "company": "Northwind Trading",
                "phone": "+20 111 111 1111",
                "notes": "Prefers email for approvals.",
            },
        )

        create_invoice(
            db,
            data={
                "client_id": acme.id,
                "title": "Operations Retainer - January",
                "amount": 850.0,
                "status": InvoiceStatus.paid,
            },
        )
        create_invoice(
            db,
            data={
                "client_id": northwind.id,
                "title": "Lead Gen Campaign Setup",
                "amount": 450.0,
                "status": InvoiceStatus.sent,
            },
        )

        has_clients = True

    # Leads
    has_leads = db.scalar(select(Lead.id).limit(1)) is not None
    if not has_leads:
        create_lead(
            db,
            data={
                "name": "Sara Ahmed",
                "email": "sara@brightlabs.io",
                "source": "Referral",
                "status": LeadStatus.contacted,
                "notes": "Asked for a proposal and timeline.",
            },
        )
        create_lead(
            db,
            data={
                "name": "Mahmoud Adel",
                "email": "mahmoud@shopzen.com",
                "source": "Website form",
                "status": LeadStatus.new,
                "notes": "Interested in invoicing + client follow-ups.",
            },
        )

    # Invoices (ensure at least one paid for dashboard revenue)
    has_invoices = db.scalar(select(Invoice.id).limit(1)) is not None
    if not has_invoices and has_clients:
        first_client = db.scalar(select(Client).limit(1))
        if first_client:
            create_invoice(
                db,
                data={
                    "client_id": first_client.id,
                    "title": "Initial Setup",
                    "amount": 250.0,
                    "status": InvoiceStatus.paid,
                },
            )
