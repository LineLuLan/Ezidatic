import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string | null;
  email: string | null;
  setAuth: (token: string, email: string) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      email: null,
      setAuth: (token, email) => {
        set({ token, email });
        if (typeof window !== "undefined") {
          window.localStorage.setItem("ezidatic_token", token);
        }
      },
      clear: () => {
        set({ token: null, email: null });
        if (typeof window !== "undefined") {
          window.localStorage.removeItem("ezidatic_token");
        }
      },
    }),
    { name: "ezidatic-auth" },
  ),
);
