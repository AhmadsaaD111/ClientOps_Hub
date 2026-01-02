<template>
  <AppLayout>
    <div class="vstack" style="gap: 16px">
      <div class="hstack" style="justify-content: space-between">
        <div>
          <div style="font-size: 20px; font-weight: 700">Dashboard</div>
          <div style="color: var(--muted); margin-top: 4px">Snapshot of clients, leads, and revenue.</div>
        </div>
        <button class="btn" @click="refresh" :disabled="loading">Refresh</button>
      </div>

      <div v-if="error" class="panel" style="border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
        {{ error }}
      </div>

      <div class="grid">
        <div class="panel">
          <div style="color: var(--muted); font-size: 13px">Total clients</div>
          <div style="font-size: 28px; font-weight: 800; margin-top: 6px">{{ metrics.totalClients }}</div>
        </div>
        <div class="panel">
          <div style="color: var(--muted); font-size: 13px">Active leads</div>
          <div style="font-size: 28px; font-weight: 800; margin-top: 6px">{{ metrics.activeLeads }}</div>
        </div>
        <div class="panel">
          <div style="color: var(--muted); font-size: 13px">Monthly revenue</div>
          <div style="font-size: 28px; font-weight: 800; margin-top: 6px">${{ metrics.monthlyRevenue.toFixed(0) }}</div>
        </div>
      </div>

      <div class="panel">
        <div class="hstack" style="justify-content: space-between">
          <div>
            <div style="font-weight: 700">Recent invoices</div>
            <div style="color: var(--muted); font-size: 13px; margin-top: 4px">Latest billing activity.</div>
          </div>
        </div>

        <table class="table" style="margin-top: 8px">
          <thead>
            <tr>
              <th>Client</th>
              <th>Title</th>
              <th>Status</th>
              <th style="text-align: right">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in recentInvoices" :key="inv.id">
              <td>{{ inv.client?.company || inv.client?.name }}</td>
              <td>{{ inv.title }}</td>
              <td>
                <span class="badge">{{ inv.status }}</span>
              </td>
              <td style="text-align: right">${{ inv.amount.toFixed(0) }}</td>
            </tr>
            <tr v-if="recentInvoices.length === 0">
              <td colspan="4" style="color: var(--muted)">No invoices yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import AppLayout from "@/components/layout/AppLayout.vue";
import { getErrorMessage } from "@/services/errors";
import { listClients } from "@/services/clients";
import { listLeads } from "@/services/leads";
import { listInvoices } from "@/services/invoices";
import type { Invoice, LeadStatus } from "@/types";

const loading = ref(false);
const error = ref<string | null>(null);

const metrics = reactive({
  totalClients: 0,
  activeLeads: 0,
  monthlyRevenue: 0
});

const invoices = ref<Invoice[]>([]);

const recentInvoices = computed(() => invoices.value.slice(0, 6));

function isActiveLead(status: LeadStatus) {
  return status === "new" || status === "contacted" || status === "qualified";
}

function computeMonthlyRevenue(items: Invoice[]) {
  const now = new Date();
  const m = now.getMonth();
  const y = now.getFullYear();

  return items
    .filter((inv) => inv.status === "paid")
    .filter((inv) => {
      const dateStr = inv.paid_at || inv.issued_at;
      const d = new Date(dateStr);
      return d.getMonth() === m && d.getFullYear() === y;
    })
    .reduce((sum, inv) => sum + inv.amount, 0);
}

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    const [clients, leads, invs] = await Promise.all([listClients(), listLeads(), listInvoices()]);
    metrics.totalClients = clients.length;
    metrics.activeLeads = leads.filter((l) => isActiveLead(l.status)).length;
    invoices.value = invs;
    metrics.monthlyRevenue = computeMonthlyRevenue(invs);
  } catch (e) {
    error.value = getErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  refresh();
});
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
