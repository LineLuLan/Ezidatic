import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-24">
      <div className="space-y-4 text-center">
        <h1 className="text-5xl font-bold tracking-tight">Ezidatic</h1>
        <p className="max-w-md text-muted-foreground">
          Upload a dataset. Get instant EDA, AutoML, and an AI agent that talks to your data.
        </p>
      </div>
      <div className="flex gap-4">
        <Button asChild>
          <Link href="/datasets">Get started</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/login">Sign in</Link>
        </Button>
      </div>
    </main>
  );
}
