import Link from "next/link";

const NAV = [
  { href: "/datasets", label: "Datasets" },
  { href: "/datasets", label: "EDA", hint: "Pick a dataset" },
  { href: "/datasets", label: "Preprocessing", hint: "Pick a dataset" },
  { href: "/datasets", label: "AutoML", hint: "Pick a dataset" },
  { href: "/datasets", label: "Chat", hint: "Pick a dataset" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 border-r bg-muted/40 p-4">
        <div className="mb-6 text-lg font-semibold">Ezidatic</div>
        <nav className="space-y-1">
          {NAV.map((item, idx) => (
            <Link
              key={`${item.label}-${idx}`}
              href={item.href}
              className="block rounded-md px-3 py-2 text-sm hover:bg-accent"
              title={item.hint}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
