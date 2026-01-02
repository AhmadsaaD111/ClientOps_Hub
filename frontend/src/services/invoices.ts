import { api } from "@/services/api";
import type { Invoice } from "@/types";

import type { PageResult } from "@/services/clients";

export async function listInvoices(): Promise<Invoice[]> {
  const resp = await api.get<Invoice[]>("/api/invoices");
  return resp.data;
}

export async function listInvoicesPage(params: {
  page: number;
  pageSize: number;
  includeArchived?: boolean;
}): Promise<PageResult<Invoice>> {
  const resp = await api.get<Invoice[]>("/api/invoices", {
    params: {
      page: params.page,
      page_size: params.pageSize,
      include_archived: params.includeArchived ? true : undefined
    }
  });

  const total = Number(resp.headers["x-total-count"] ?? 0);
  const page = Number(resp.headers["x-page"] ?? params.page);
  const pageSize = Number(resp.headers["x-page-size"] ?? params.pageSize);
  const totalPages = Number(resp.headers["x-total-pages"] ?? 0);

  return { items: resp.data, total, page, pageSize, totalPages };
}

export async function createInvoice(payload: Omit<Invoice, "id" | "issued_at" | "paid_at" | "client">): Promise<Invoice> {
  const resp = await api.post<Invoice>("/api/invoices", payload);
  return resp.data;
}

export async function updateInvoice(
  id: number,
  payload: Omit<Invoice, "id" | "issued_at" | "paid_at" | "client">
): Promise<Invoice> {
  const resp = await api.put<Invoice>(`/api/invoices/${id}`, payload);
  return resp.data;
}

export async function deleteInvoice(id: number): Promise<void> {
  await api.delete(`/api/invoices/${id}`);
}

export async function restoreInvoice(id: number): Promise<Invoice> {
  const resp = await api.post<Invoice>(`/api/invoices/${id}/restore`);
  return resp.data;
}
