import { api } from "@/services/api";
import type { Lead } from "@/types";

import type { PageResult } from "@/services/clients";

export async function listLeads(): Promise<Lead[]> {
  const resp = await api.get<Lead[]>("/api/leads");
  return resp.data;
}

export async function listLeadsPage(params: {
  page: number;
  pageSize: number;
  includeArchived?: boolean;
}): Promise<PageResult<Lead>> {
  const resp = await api.get<Lead[]>("/api/leads", {
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

export async function createLead(payload: Omit<Lead, "id" | "created_at">): Promise<Lead> {
  const resp = await api.post<Lead>("/api/leads", payload);
  return resp.data;
}

export async function updateLead(id: number, payload: Omit<Lead, "id" | "created_at">): Promise<Lead> {
  const resp = await api.put<Lead>(`/api/leads/${id}`, payload);
  return resp.data;
}

export async function deleteLead(id: number): Promise<void> {
  await api.delete(`/api/leads/${id}`);
}

export async function restoreLead(id: number): Promise<Lead> {
  const resp = await api.post<Lead>(`/api/leads/${id}/restore`);
  return resp.data;
}
