import Link from "next/link";

const NAV = [
  { href: "/datasets", label: "Datasets" },
  { href: "/eda/_", label: "EDA" },
  { href: "/ml/_", label: "AutoML" },
  { href: "/chat/_", label: "Chat" },
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
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-md px-3 py-2 text-sm hover:bg-accent"
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
