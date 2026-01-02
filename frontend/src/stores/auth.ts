import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { api, setAuthToken } from "@/services/api";
import type { UserPublic, UserRole } from "@/types";

const STORAGE_KEY = "clientops_auth_token";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem(STORAGE_KEY));
  const user = ref<UserPublic | null>(null);
  const loading = ref(false);

  if (token.value) {
    setAuthToken(token.value);
  }

  const isAuthenticated = computed(() => Boolean(token.value));
  const role = computed<UserRole | null>(() => user.value?.role ?? null);
  const isAdmin = computed(() => role.value === "admin");

  async function login(username: string, password: string) {
    loading.value = true;
    try {
      const body = new URLSearchParams();
      body.set("username", username);
      body.set("password", password);

      const resp = await api.post("/api/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });

      token.value = resp.data.access_token;
      localStorage.setItem(STORAGE_KEY, token.value);
      setAuthToken(token.value);

      await fetchMe();
    } finally {
      loading.value = false;
    }
  }

  async function fetchMe() {
    if (!token.value) return;
    setAuthToken(token.value);
    const resp = await api.get<UserPublic>("/api/auth/me");
    user.value = resp.data;
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem(STORAGE_KEY);
    setAuthToken(null);
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    role,
    isAdmin,
    login,
    fetchMe,
    logout
  };
});
