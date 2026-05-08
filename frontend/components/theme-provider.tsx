"use client";

import { ThemeProvider as NextThemesProvider, type ThemeProviderProps } from "next-themes";

/**
 * App-wide theme context. Wraps `next-themes` so the app only depends
 * on a single import path, and so we can swap providers later without
 * touching every consumer.
 */
export function ThemeProvider(props: ThemeProviderProps) {
  return <NextThemesProvider {...props} />;
}
