<template>
  <AppLayout>
    <div class="vstack" style="gap: 16px">
      <div class="hstack" style="justify-content: space-between; flex-wrap: wrap">
        <div>
          <div style="font-size: 20px; font-weight: 700">Invoices</div>
          <div style="color: var(--muted); margin-top: 4px">Create invoices tied to clients.</div>
        </div>
        <button class="btn btn-primary" @click="startCreate">New invoice</button>
      </div>

      <div v-if="error" class="panel" style="border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
        {{ error }}
      </div>

      <div class="panel">
        <div v-if="auth.isAdmin" class="hstack" style="justify-content: flex-end; margin-bottom: 10px">
          <label class="hstack" style="gap: 8px; align-items: center">
            <input type="checkbox" v-model="showArchived" @change="onToggleArchived" />
            <span style="color: var(--muted); font-size: 13px">Show archived</span>
          </label>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th>Client</th>
              <th>Title</th>
              <th>Status</th>
              <th style="text-align: right">Amount</th>
              <th style="width: 240px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in invoices" :key="inv.id">
              <td style="font-weight: 600">{{ inv.client?.company || inv.client?.name }}</td>
              <td>
                {{ inv.title }}
                <span v-if="inv.deleted_at" class="badge" style="margin-left: 8px">archived</span>
              </td>
              <td>
                <select
                  class="input"
                  style="max-width: 140px"
                  v-model="inv.status"
                  @change="onStatusChange(inv)"
                  :disabled="Boolean(inv.deleted_at)"
                >
                  <option value="draft">draft</option>
                  <option value="sent">sent</option>
                  <option value="paid">paid</option>
                </select>
              </td>
              <td style="text-align: right">${{ inv.amount.toFixed(0) }}</td>
              <td style="text-align: right">
                <div class="hstack" style="justify-content: flex-end">
                  <button class="btn" @click="startEdit(inv)" :disabled="Boolean(inv.deleted_at)">Edit</button>
                  <button
                    v-if="auth.isAdmin && !inv.deleted_at"
                    class="btn btn-danger"
                    @click="onArchive(inv.id)"
                  >
                    Archive
                  </button>
                  <button v-if="auth.isAdmin && inv.deleted_at" class="btn" @click="onRestore(inv.id)">Restore</button>
                </div>
              </td>
            </tr>
            <tr v-if="invoices.length === 0">
              <td colspan="5" style="color: var(--muted)">No invoices found.</td>
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

      <div v-if="form.open" class="panel">
        <div class="hstack" style="justify-content: space-between">
          <div style="font-weight: 700">{{ form.mode === "create" ? "New invoice" : "Edit invoice" }}</div>
          <button class="btn" @click="closeForm">Close</button>
        </div>

        <hr class="hr" style="margin: 12px 0" />

        <form class="grid" @submit.prevent="onSubmit">
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Client</div>
            <select class="input" v-model.number="form.data.client_id" required>
              <option v-for="c in clients" :key="c.id" :value="c.id">
                {{ c.company || c.name }}
              </option>
            </select>
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Status</div>
            <select class="input" v-model="form.data.status">
              <option value="draft">draft</option>
              <option value="sent">sent</option>
              <option value="paid">paid</option>
            </select>
          </div>
          <div style="grid-column: 1 / -1">
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Title</div>
            <input class="input" v-model.trim="form.data.title" required />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Amount</div>
            <input class="input" type="number" min="1" step="1" v-model.number="form.data.amount" required />
          </div>

          <div v-if="formError" class="panel" style="grid-column: 1 / -1; border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
            {{ formError }}
          </div>

          <div class="hstack" style="grid-column: 1 / -1; justify-content: flex-end">
            <button class="btn btn-primary" type="submit" :disabled="saving">
              {{ saving ? "Saving..." : "Save" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import AppLayout from "@/components/layout/AppLayout.vue";
import { useAuthStore } from "@/stores/auth";
import type { Client, Invoice, InvoiceStatus } from "@/types";
import { getErrorMessage } from "@/services/errors";
import { listClients } from "@/services/clients";
import { createInvoice, deleteInvoice, listInvoicesPage, restoreInvoice, updateInvoice } from "@/services/invoices";

const auth = useAuthStore();

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const formError = ref<string | null>(null);

const clients = ref<Client[]>([]);
const invoices = ref<Invoice[]>([]);

const showArchived = ref(false);

const page = ref(1);
const pageSize = ref(10);
const total = ref(0);
const totalPages = ref(1);

const startItem = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1));
const endItem = computed(() => Math.min(total.value, page.value * pageSize.value));

const emptyPayload = (clientId: number | null) => ({
  client_id: clientId ?? 0,
  title: "",
  amount: 0,
  status: "draft" as InvoiceStatus
});

const form = reactive({
  open: false,
  mode: "create" as "create" | "edit",
  id: null as number | null,
  data: emptyPayload(null)
});

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    const [c, inv] = await Promise.all([
      listClients(),
      listInvoicesPage({
        page: page.value,
        pageSize: pageSize.value,
        includeArchived: showArchived.value && auth.isAdmin
      })
    ]);
    clients.value = c;
    invoices.value = inv.items;
    total.value = inv.total;
    totalPages.value = inv.totalPages || 1;
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

function onToggleArchived() {
  page.value = 1;
  refresh();
}

function startCreate() {
  if (clients.value.length === 0) {
    error.value = "Create a client before creating an invoice.";
    return;
  }

  form.open = true;
  form.mode = "create";
  form.id = null;
  form.data = emptyPayload(clients.value[0].id);
  formError.value = null;
}

function startEdit(inv: Invoice) {
  form.open = true;
  form.mode = "edit";
  form.id = inv.id;
  form.data = {
    client_id: inv.client_id,
    title: inv.title,
    amount: inv.amount,
    status: inv.status
  };
  formError.value = null;
}

function closeForm() {
  form.open = false;
}

async function onSubmit() {
  saving.value = true;
  formError.value = null;
  try {
    const payload = {
      client_id: form.data.client_id,
      title: form.data.title,
      amount: form.data.amount,
      status: form.data.status
    };

    if (form.mode === "create") {
      await createInvoice(payload);
    } else if (form.id != null) {
      await updateInvoice(form.id, payload);
    }

    form.open = false;
    page.value = 1;
    await refresh();
  } catch (e) {
    formError.value = getErrorMessage(e);
  } finally {
    saving.value = false;
  }
}

async function onStatusChange(inv: Invoice) {
  try {
    const payload = {
      client_id: inv.client_id,
      title: inv.title,
      amount: inv.amount,
      status: inv.status
    };
    await updateInvoice(inv.id, payload);
  } catch (e) {
    error.value = getErrorMessage(e);
    await refresh();
  }
}

async function onArchive(id: number) {
  if (!confirm("Archive this invoice?")) return;
  error.value = null;
  try {
    await deleteInvoice(id);
    await refresh();
  } catch (e) {
    error.value = getErrorMessage(e);
  }
}

async function onRestore(id: number) {
  error.value = null;
  try {
    await restoreInvoice(id);
    await refresh();
  } catch (e) {
    error.value = getErrorMessage(e);
  }
}

onMounted(() => {
  refresh();
});
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
