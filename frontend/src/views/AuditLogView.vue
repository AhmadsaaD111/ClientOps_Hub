<template>
  <AppLayout>
    <div class="vstack" style="gap: 16px">
      <div class="hstack" style="justify-content: space-between; flex-wrap: wrap">
        <div>
          <div style="font-size: 20px; font-weight: 700">Audit log</div>
          <div style="color: var(--muted); margin-top: 4px">Admin-only record of write actions.</div>
        </div>
        <button class="btn" @click="refresh" :disabled="loading">Refresh</button>
      </div>

      <div v-if="!auth.isAdmin" class="panel" style="border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
        Admin privileges are required for this page.
      </div>

      <div v-else>
        <div v-if="error" class="panel" style="border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
          {{ error }}
        </div>

        <div class="panel">
          <table class="table">
            <thead>
              <tr>
                <th style="width: 180px">Time</th>
                <th style="width: 110px">Entity</th>
                <th style="width: 90px">ID</th>
                <th style="width: 140px">Action</th>
                <th style="width: 150px">Actor</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.id">
                <td>{{ formatTs(row.timestamp) }}</td>
                <td>{{ row.entity_type }}</td>
                <td>{{ row.entity_id }}</td>
                <td><span class="badge">{{ row.action }}</span></td>
                <td>{{ row.actor_role }} #{{ row.actor_user_id }}</td>
                <td>{{ row.summary || "—" }}</td>
              </tr>
              <tr v-if="rows.length === 0">
                <td colspan="6" style="color: var(--muted)">No audit logs yet.</td>
              </tr>
            </tbody>
          </table>

          <div class="hstack" style="justify-content: space-between; margin-top: 12px; flex-wrap: wrap">
            <div style="color: var(--muted); font-size: 13px">
              {{ total === 0 ? "0" : startItem }}–{{ endItem }} of {{ total }}
            </div>
            <div class="hstack">
              <button class="btn" @click="prevPage" :disabled="loading || page <= 1">Prev</button>
              <span class="badge">Page {{ page }} / {{ totalPages }}</span>
              <button class="btn" @click="nextPage" :disabled="loading || page >= totalPages">Next</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import AppLayout from "@/components/layout/AppLayout.vue";
import { getErrorMessage } from "@/services/errors";
import { listAuditLogsPage, type AuditLog } from "@/services/auditLogs";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const loading = ref(false);
const error = ref<string | null>(null);

const rows = ref<AuditLog[]>([]);

const page = ref(1);
const pageSize = ref(15);
const total = ref(0);
const totalPages = ref(1);

const startItem = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1));
const endItem = computed(() => Math.min(total.value, page.value * pageSize.value));

function formatTs(value: string) {
  const d = new Date(value);
  return isNaN(d.getTime()) ? value : d.toLocaleString();
}

async function refresh() {
  if (!auth.isAdmin) return;
  loading.value = true;
  error.value = null;
  try {
    const resp = await listAuditLogsPage({ page: page.value, pageSize: pageSize.value });
    rows.value = resp.items;
    total.value = resp.total;
    totalPages.value = resp.totalPages || 1;
  } catch (e) {
    error.value = getErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

function prevPage() {
  if (page.value <= 1) return;
  page.value -= 1;
  refresh();
}

function nextPage() {
  if (page.value >= totalPages.value) return;
  page.value += 1;
  refresh();
}

onMounted(() => {
  refresh();
});
</script>
