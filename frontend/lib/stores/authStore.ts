import { create } from "zustand";
import { persist } from "zustand/middleware";

import { clearToken, setToken } from "@/lib/api-client";

interface AuthState {
  token: string | null;
  email: string | null;
  hydrated: boolean;
  setAuth: (token: string, email: string) => void;
  clear: () => void;
  setHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      email: null,
      hydrated: false,
      setAuth: (token, email) => {
        set({ token, email });
        setToken(token);
      },
      clear: () => {
        set({ token: null, email: null });
        clearToken();
      },
      setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "ezidatic-auth",
      onRehydrateStorage: () => (state) => state?.setHydrated(),
    },
  ),
);
