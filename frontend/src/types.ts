export type UserRole = "admin" | "staff";

export interface UserPublic {
  id: number;
  username: string;
  role: UserRole;
}

export interface Client {
  id: number;
  name: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  notes?: string | null;
  created_at: string;
  deleted_at?: string | null;
}

export type LeadStatus = "new" | "contacted" | "qualified" | "lost";

export interface Lead {
  id: number;
  name: string;
  email?: string | null;
  source?: string | null;
  status: LeadStatus;
  notes?: string | null;
  created_at: string;
  deleted_at?: string | null;
}

export type InvoiceStatus = "draft" | "sent" | "paid";

export interface Invoice {
  id: number;
  client_id: number;
  title: string;
  amount: number;
  status: InvoiceStatus;
  issued_at: string;
  paid_at?: string | null;
  client: Client;
  deleted_at?: string | null;
}
