import { createRouter, createWebHistory } from "vue-router";

import { useAuthStore } from "@/stores/auth";

import LoginView from "@/views/LoginView.vue";
import DashboardView from "@/views/DashboardView.vue";
import ClientsView from "@/views/ClientsView.vue";
import LeadsView from "@/views/LeadsView.vue";
import InvoicesView from "@/views/InvoicesView.vue";
import AuditLogView from "@/views/AuditLogView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/login", component: LoginView, meta: { public: true } },
    { path: "/dashboard", component: DashboardView },
    { path: "/clients", component: ClientsView },
    { path: "/leads", component: LeadsView },
    { path: "/invoices", component: InvoicesView },
    { path: "/audit-logs", component: AuditLogView, meta: { admin: true } }
  ]
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();

  if (to.path === "/login" && auth.isAuthenticated) {
    const next = typeof to.query.next === "string" ? to.query.next : "/dashboard";
    return next;
  }

  if (to.meta.public) return true;

  if (!auth.isAuthenticated) {
    return { path: "/login", query: { next: to.fullPath } };
  }

  if (auth.isAuthenticated && !auth.user) {
    try {
      await auth.fetchMe();
    } catch {
      auth.logout();
      return { path: "/login", query: { next: to.fullPath } };
    }
  }

  if (to.meta.admin && auth.role !== "admin") {
    return { path: "/dashboard" };
  }

  return true;
});

export default router;
