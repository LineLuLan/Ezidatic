import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";

const NAV = [
  { href: "/datasets", label: "Datasets" },
  { href: "/datasets", label: "EDA", hint: "Pick a dataset" },
  { href: "/datasets", label: "Preprocessing", hint: "Pick a dataset" },
  { href: "/datasets", label: "AutoML", hint: "Pick a dataset" },
  { href: "/datasets", label: "Chat", hint: "Pick a dataset" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 flex-col border-r bg-muted/40 p-4">
        <div className="mb-6 text-lg font-semibold">Ezidatic</div>
        <nav className="space-y-1" aria-label="Primary">
          {NAV.map((item, idx) => (
            <Link
              key={`${item.label}-${idx}`}
              href={item.href}
              className="block rounded-md px-3 py-2 text-sm hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              title={item.hint}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="mt-auto flex items-center justify-between pt-4">
          <span className="text-xs text-muted-foreground">Theme</span>
          <ThemeToggle />
        </div>
      </aside>
      <main id="content" className="flex-1 p-8">
        {children}
      </main>
    </div>
  );
}
