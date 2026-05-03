"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { ApiError, api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/authStore";

interface Credentials {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const router = useRouter();
  return useMutation<TokenResponse, ApiError, Credentials>({
    mutationFn: (creds) =>
      api<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(creds),
      }),
    onSuccess: (data, vars) => {
      setAuth(data.access_token, vars.email);
      router.push("/datasets");
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const router = useRouter();
  return useMutation<TokenResponse, ApiError, Credentials>({
    mutationFn: (creds) =>
      api<TokenResponse>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(creds),
      }),
    onSuccess: (data, vars) => {
      setAuth(data.access_token, vars.email);
      router.push("/datasets");
    },
  });
}

export function useLogout() {
  const clear = useAuthStore((s) => s.clear);
  const router = useRouter();
  return () => {
    clear();
    router.push("/login");
  };
}
