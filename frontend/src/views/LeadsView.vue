<template>
  <AppLayout>
    <div class="vstack" style="gap: 16px">
      <div class="hstack" style="justify-content: space-between; flex-wrap: wrap">
        <div>
          <div style="font-size: 20px; font-weight: 700">Leads</div>
          <div style="color: var(--muted); margin-top: 4px">Move leads through a simple pipeline.</div>
        </div>
        <div class="hstack" style="gap: 10px">
          <label v-if="auth.isAdmin" class="hstack" style="gap: 8px; align-items: center">
            <input type="checkbox" v-model="showArchived" @change="onToggleArchived" />
            <span style="color: var(--muted); font-size: 13px">Show archived</span>
          </label>
          <button class="btn btn-primary" @click="startCreate">New lead</button>
        </div>
      </div>

      <div v-if="error" class="panel" style="border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
        {{ error }}
      </div>

      <div class="pipeline">
        <div v-for="s in statuses" :key="s" class="panel">
          <div class="hstack" style="justify-content: space-between">
            <div style="font-weight: 700; text-transform: capitalize">{{ s }}</div>
            <span class="badge">{{ grouped[s].length }}</span>
          </div>

          <div class="vstack" style="margin-top: 10px">
            <div v-for="l in grouped[s]" :key="l.id" class="card">
              <div class="hstack" style="justify-content: space-between">
                <div style="font-weight: 700">
                  {{ l.name }}
                  <span v-if="l.deleted_at" class="badge" style="margin-left: 8px">archived</span>
                </div>
                <button class="btn" @click="startEdit(l)" :disabled="Boolean(l.deleted_at)">Edit</button>
              </div>
              <div style="color: var(--muted); font-size: 13px; margin-top: 4px">
                {{ l.email || "No email" }} · {{ l.source || "Unknown source" }}
              </div>

              <div class="hstack" style="margin-top: 10px; justify-content: space-between">
                <select
                  class="input"
                  style="max-width: 160px"
                  v-model="l.status"
                  @change="onStatusChange(l)"
                  :disabled="Boolean(l.deleted_at)"
                >
                  <option v-for="o in statuses" :key="o" :value="o">{{ o }}</option>
                </select>
                <div class="hstack" style="justify-content: flex-end">
                  <button class="btn btn-danger" @click="onArchive(l.id)" :disabled="Boolean(l.deleted_at)">Archive</button>
                  <button v-if="auth.isAdmin && l.deleted_at" class="btn" @click="onRestore(l.id)">Restore</button>
                </div>
              </div>
            </div>

            <div v-if="grouped[s].length === 0" style="color: var(--muted); font-size: 13px">
              No leads in this stage.
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="hstack" style="justify-content: space-between; flex-wrap: wrap">
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
          <div style="font-weight: 700">{{ form.mode === "create" ? "New lead" : "Edit lead" }}</div>
          <button class="btn" @click="closeForm">Close</button>
        </div>

        <hr class="hr" style="margin: 12px 0" />

        <form class="grid" @submit.prevent="onSubmit">
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Name</div>
            <input class="input" v-model.trim="form.data.name" required />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Email</div>
            <input class="input" v-model.trim="form.data.email" />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Source</div>
            <input class="input" v-model.trim="form.data.source" />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Status</div>
            <select class="input" v-model="form.data.status">
              <option v-for="o in statuses" :key="o" :value="o">{{ o }}</option>
            </select>
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
import type { Lead, LeadStatus } from "@/types";
import { getErrorMessage } from "@/services/errors";
import { createLead, deleteLead, listLeadsPage, restoreLead, updateLead } from "@/services/leads";

const statuses: LeadStatus[] = ["new", "contacted", "qualified", "lost"];

const auth = useAuthStore();

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const formError = ref<string | null>(null);

const leads = ref<Lead[]>([]);

const showArchived = ref(false);

const page = ref(1);
const pageSize = ref(12);
const total = ref(0);
const totalPages = ref(1);

const startItem = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1));
const endItem = computed(() => Math.min(total.value, page.value * pageSize.value));

const grouped = computed<Record<LeadStatus, Lead[]>>(() => {
  const base: Record<LeadStatus, Lead[]> = {
    new: [],
    contacted: [],
    qualified: [],
    lost: []
  };

  for (const l of leads.value) {
    base[l.status].push(l);
  }
  return base;
});

const emptyPayload = () => ({
  name: "",
  email: "",
  source: "",
  status: "new" as LeadStatus,
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
    const resp = await listLeadsPage({
      page: page.value,
      pageSize: pageSize.value,
      includeArchived: showArchived.value && auth.isAdmin
    });
    leads.value = resp.items;
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

function onToggleArchived() {
  page.value = 1;
  refresh();
}

function startCreate() {
  form.open = true;
  form.mode = "create";
  form.id = null;
  form.data = emptyPayload();
  formError.value = null;
}

function startEdit(l: Lead) {
  form.open = true;
  form.mode = "edit";
  form.id = l.id;
  form.data = {
    name: l.name,
    email: l.email ?? "",
    source: l.source ?? "",
    status: l.status,
    notes: l.notes ?? ""
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
      source: form.data.source || null,
      status: form.data.status,
      notes: form.data.notes || null
    };

    if (form.mode === "create") {
      await createLead(payload);
    } else if (form.id != null) {
      await updateLead(form.id, payload);
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

async function onStatusChange(l: Lead) {
  try {
    const payload = {
      name: l.name,
      email: l.email ?? null,
      source: l.source ?? null,
      status: l.status,
      notes: l.notes ?? null
    };
    await updateLead(l.id, payload);
  } catch (e) {
    error.value = getErrorMessage(e);
    await refresh();
  }
}

async function onArchive(id: number) {
  if (!confirm("Archive this lead?")) return;
  error.value = null;
  try {
    await deleteLead(id);
    await refresh();
  } catch (e) {
    error.value = getErrorMessage(e);
  }
}

async function onRestore(id: number) {
  error.value = null;
  try {
    await restoreLead(id);
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
.pipeline {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 1100px) {
  .pipeline {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .pipeline {
    grid-template-columns: 1fr;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
