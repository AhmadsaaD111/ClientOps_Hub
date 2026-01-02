from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import InvoiceStatus, LeadStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole


class ClientBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    deleted_at: datetime | None = None


class LeadBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr | None = None
    source: str | None = Field(default=None, max_length=200)
    status: LeadStatus = LeadStatus.new
    notes: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(LeadBase):
    pass


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    deleted_at: datetime | None = None


class InvoiceBase(BaseModel):
    client_id: int
    title: str = Field(min_length=2, max_length=200)
    amount: float = Field(gt=0)
    status: InvoiceStatus = InvoiceStatus.draft


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(InvoiceBase):
    paid_at: datetime | None = None


class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issued_at: datetime
    paid_at: datetime | None
    deleted_at: datetime | None = None


class InvoiceReadWithClient(InvoiceRead):
    client: ClientRead


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    entity_type: str
    entity_id: int
    action: str
    actor_user_id: int
    actor_role: str
    timestamp: datetime = Field(alias="created_at")
    summary: str | None = None
