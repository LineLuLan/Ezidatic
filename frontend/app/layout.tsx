import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";
import { SkipToContent } from "@/components/skip-to-content";
import { ThemeProvider } from "@/components/theme-provider";

export const metadata: Metadata = {
  title: "Ezidatic — AI Data Analyst",
  description:
    "Upload a dataset. Get instant EDA, AutoML, and an AI agent that talks to your data.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <SkipToContent />
          <QueryProvider>{children}</QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
