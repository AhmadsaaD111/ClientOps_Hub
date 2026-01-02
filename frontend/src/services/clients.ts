import { api } from "@/services/api";
import type { Client } from "@/types";

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export async function listClients(q?: string): Promise<Client[]> {
  const resp = await api.get<Client[]>("/api/clients", { params: q ? { q } : undefined });
  return resp.data;
}

export async function listClientsPage(params: {
  q?: string;
  page: number;
  pageSize: number;
  includeArchived?: boolean;
}): Promise<PageResult<Client>> {
  const resp = await api.get<Client[]>("/api/clients", {
    params: {
      q: params.q,
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

export async function createClient(payload: Omit<Client, "id" | "created_at">): Promise<Client> {
  const resp = await api.post<Client>("/api/clients", payload);
  return resp.data;
}

export async function updateClient(id: number, payload: Omit<Client, "id" | "created_at">): Promise<Client> {
  const resp = await api.put<Client>(`/api/clients/${id}`, payload);
  return resp.data;
}

export async function deleteClient(id: number): Promise<void> {
  await api.delete(`/api/clients/${id}`);
}

export async function restoreClient(id: number): Promise<Client> {
  const resp = await api.post<Client>(`/api/clients/${id}/restore`);
  return resp.data;
}
