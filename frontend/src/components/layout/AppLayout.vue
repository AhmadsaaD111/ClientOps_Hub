<template>
  <div>
    <header class="header">
      <div class="container header-inner">
        <div class="brand">
          <div class="logo">CO</div>
          <div class="brand-text">
            <div class="title">ClientOps Hub</div>
            <div class="subtitle">Client operations workspace</div>
          </div>
        </div>

        <nav class="nav">
          <RouterLink class="nav-link" to="/dashboard">Dashboard</RouterLink>
          <RouterLink class="nav-link" to="/clients">Clients</RouterLink>
          <RouterLink class="nav-link" to="/leads">Leads</RouterLink>
          <RouterLink class="nav-link" to="/invoices">Invoices</RouterLink>
          <RouterLink v-if="auth.isAdmin" class="nav-link" to="/audit-logs">Audit log</RouterLink>
        </nav>

        <div class="hstack" style="gap: 10px">
          <span class="badge" v-if="auth.user">{{ auth.user.username }} · {{ auth.user.role }}</span>
          <button class="btn" @click="onLogout">Logout</button>
        </div>
      </div>
    </header>

    <main class="container" style="padding: 22px 0 40px">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

function onLogout() {
  auth.logout();
  router.push("/login");
}
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  background: rgba(11, 18, 32, 0.65);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  background: rgba(79, 140, 255, 0.18);
  border: 1px solid rgba(79, 140, 255, 0.35);
}

.brand-text .title {
  font-weight: 700;
  line-height: 1.1;
}

.brand-text .subtitle {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.1;
  margin-top: 2px;
}

.nav {
  display: flex;
  gap: 10px;
}

.nav-link {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid transparent;
  color: var(--muted);
}

.nav-link.router-link-active {
  color: var(--text);
  border-color: var(--border);
  background: rgba(255, 255, 255, 0.03);
}
</style>
