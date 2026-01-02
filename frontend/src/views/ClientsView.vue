<template>
  <AppLayout>
    <div class="vstack" style="gap: 16px">
      <div class="hstack" style="justify-content: space-between; flex-wrap: wrap">
        <div>
          <div style="font-size: 20px; font-weight: 700">Clients</div>
          <div style="color: var(--muted); margin-top: 4px">Track relationships and core contact details.</div>
        </div>
        <button class="btn btn-primary" @click="startCreate">New client</button>
      </div>

      <div class="panel">
        <div class="hstack" style="justify-content: space-between; gap: 10px; flex-wrap: wrap">
          <input class="input" style="max-width: 420px" placeholder="Search by name or company..." v-model.trim="search" @keyup.enter="refresh" />
          <div class="hstack">
            <label v-if="auth.isAdmin" class="hstack" style="gap: 8px; align-items: center">
              <input type="checkbox" v-model="showArchived" @change="onToggleArchived" />
              <span style="color: var(--muted); font-size: 13px">Show archived</span>
            </label>
            <button class="btn" @click="refresh" :disabled="loading">Search</button>
            <button class="btn" @click="reset">Reset</button>
          </div>
        </div>

        <div v-if="error" class="panel" style="margin-top: 12px; border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
          {{ error }}
        </div>

        <table class="table" style="margin-top: 10px">
          <thead>
            <tr>
              <th>Name</th>
              <th>Company</th>
              <th>Email</th>
              <th>Phone</th>
              <th style="width: 220px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in clients" :key="c.id">
              <td style="font-weight: 600">
                {{ c.name }}
                <span v-if="c.deleted_at" class="badge" style="margin-left: 8px">archived</span>
              </td>
              <td>{{ c.company || "—" }}</td>
              <td>{{ c.email || "—" }}</td>
              <td>{{ c.phone || "—" }}</td>
              <td style="text-align: right">
                <div class="hstack" style="justify-content: flex-end">
                  <button class="btn" @click="startEdit(c)" :disabled="Boolean(c.deleted_at)">Edit</button>
                  <button
                    v-if="auth.isAdmin && !c.deleted_at"
                    class="btn btn-danger"
                    @click="onArchive(c.id)"
                  >
                    Archive
                  </button>
                  <button v-if="auth.isAdmin && c.deleted_at" class="btn" @click="onRestore(c.id)">Restore</button>
                </div>
              </td>
            </tr>
            <tr v-if="clients.length === 0">
              <td colspan="5" style="color: var(--muted)">No clients found.</td>
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
          <div style="font-weight: 700">{{ form.mode === "create" ? "New client" : "Edit client" }}</div>
          <button class="btn" @click="closeForm">Close</button>
        </div>

        <hr class="hr" style="margin: 12px 0" />

        <form class="grid" @submit.prevent="onSubmit">
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Name</div>
            <input class="input" v-model.trim="form.data.name" required />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Company</div>
            <input class="input" v-model.trim="form.data.company" />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Email</div>
            <input class="input" v-model.trim="form.data.email" />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Phone</div>
            <input class="input" v-model.trim="form.data.phone" />
          </div>
          <div style="grid-column: 1 / -1">
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Notes</div>
            <textarea class="input" rows="3" v-model.trim="form.data.notes" />
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
import type { Client } from "@/types";
import { getErrorMessage } from "@/services/errors";
import { createClient, deleteClient, listClientsPage, restoreClient, updateClient } from "@/services/clients";

const auth = useAuthStore();

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const formError = ref<string | null>(null);

const search = ref("");
const clients = ref<Client[]>([]);

const showArchived = ref(false);

const page = ref(1);
const pageSize = ref(10);
const total = ref(0);
const totalPages = ref(1);

const startItem = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1));
const endItem = computed(() => Math.min(total.value, page.value * pageSize.value));

const emptyPayload = () => ({
  name: "",
  email: "",
  phone: "",
  company: "",
  notes: ""
});

const form = reactive({
  open: false,
  mode: "create" as "create" | "edit",
  id: null as number | null,
  data: emptyPayload()
});

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    const resp = await listClientsPage({
      q: search.value || undefined,
      page: page.value,
      pageSize: pageSize.value,
      includeArchived: showArchived.value && auth.isAdmin
    });
    clients.value = resp.items;
    total.value = resp.total;
    totalPages.value = resp.totalPages || 1;
  } catch (e) {
    error.value = getErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

function reset() {
  search.value = "";
  showArchived.value = false;
  page.value = 1;
  refresh();
}

function onToggleArchived() {
  page.value = 1;
  refresh();
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

function startCreate() {
  form.open = true;
  form.mode = "create";
  form.id = null;
  form.data = emptyPayload();
  formError.value = null;
}

function startEdit(c: Client) {
  form.open = true;
  form.mode = "edit";
  form.id = c.id;
  form.data = {
    name: c.name,
    email: c.email ?? "",
    phone: c.phone ?? "",
    company: c.company ?? "",
    notes: c.notes ?? ""
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
      name: form.data.name,
      email: form.data.email || null,
      phone: form.data.phone || null,
      company: form.data.company || null,
      notes: form.data.notes || null
    };

    if (form.mode === "create") {
      await createClient(payload);
    } else if (form.id != null) {
      await updateClient(form.id, payload);
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

async function onArchive(id: number) {
  if (!confirm("Archive this client? This will also archive related invoices.")) return;
  error.value = null;
  try {
    await deleteClient(id);
    await refresh();
  } catch (e) {
    error.value = getErrorMessage(e);
  }
}

async function onRestore(id: number) {
  error.value = null;
  try {
    await restoreClient(id);
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
