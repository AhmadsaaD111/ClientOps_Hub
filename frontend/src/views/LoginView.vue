<template>
  <div class="container" style="padding: 70px 0">
    <div class="panel" style="max-width: 520px; margin: 0 auto">
      <div class="vstack" style="gap: 14px">
        <div>
          <div style="font-size: 20px; font-weight: 700">Sign in</div>
          <div style="color: var(--muted); margin-top: 4px">
            Access your client operations workspace.
          </div>
        </div>

        <div class="panel" style="background: rgba(255,255,255,0.03)">
          <div style="color: var(--muted); font-size: 13px; margin-bottom: 8px">Default accounts</div>
          <div class="hstack" style="justify-content: space-between">
            <div>
              <div style="font-weight: 600">Admin</div>
              <div style="color: var(--muted); font-size: 13px">admin / admin123</div>
            </div>
            <div>
              <div style="font-weight: 600">Staff</div>
              <div style="color: var(--muted); font-size: 13px">staff / staff123</div>
            </div>
          </div>
        </div>

        <form class="vstack" @submit.prevent="onSubmit" style="gap: 12px">
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Username</div>
            <input class="input" v-model.trim="username" autocomplete="username" />
          </div>
          <div>
            <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px">Password</div>
            <input class="input" type="password" v-model="password" autocomplete="current-password" />
          </div>

          <div v-if="error" class="panel" style="border-color: rgba(255,92,115,0.35); background: rgba(255,92,115,0.08)">
            {{ error }}
          </div>

          <button class="btn btn-primary" type="submit" :disabled="auth.loading">
            {{ auth.loading ? "Signing in..." : "Sign in" }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";
import { getErrorMessage } from "@/services/errors";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const username = ref("");
const password = ref("");
const error = ref<string | null>(null);

async function onSubmit() {
  error.value = null;
  try {
    await auth.login(username.value, password.value);
    const next = typeof route.query.next === "string" ? route.query.next : "/dashboard";
    await router.replace(next);
  } catch (e) {
    error.value = getErrorMessage(e);
  }
}
</script>
