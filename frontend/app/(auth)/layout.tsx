export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main id="content" className="flex min-h-screen items-center justify-center bg-muted/40 p-6">
      <div className="w-full max-w-sm">{children}</div>
    </main>
  );
}
