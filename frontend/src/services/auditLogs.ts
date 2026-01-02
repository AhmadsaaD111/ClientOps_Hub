import { api } from "@/services/api";

import type { PageResult } from "@/services/clients";

export interface AuditLog {
  id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  actor_user_id: number;
  actor_role: string;
  timestamp: string;
  summary?: string | null;
}

export async function listAuditLogsPage(params: { page: number; pageSize: number }): Promise<PageResult<AuditLog>> {
  const resp = await api.get<AuditLog[]>("/api/audit-logs", {
    params: {
      page: params.page,
      page_size: params.pageSize
    }
  });

  const total = Number(resp.headers["x-total-count"] ?? 0);
  const page = Number(resp.headers["x-page"] ?? params.page);
  const pageSize = Number(resp.headers["x-page-size"] ?? params.pageSize);
  const totalPages = Number(resp.headers["x-total-pages"] ?? 0);

  return { items: resp.data, total, page, pageSize, totalPages };
}
