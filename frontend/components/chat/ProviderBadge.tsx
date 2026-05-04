const COLORS: Record<string, string> = {
  groq: "bg-orange-100 text-orange-800",
  gemini: "bg-blue-100 text-blue-800",
  openrouter: "bg-purple-100 text-purple-800",
  ollama: "bg-emerald-100 text-emerald-800",
};

export function ProviderBadge({ provider }: { provider: string | null }) {
  if (!provider) return null;
  const cls = COLORS[provider] ?? "bg-gray-100 text-gray-800";
  return (
    <span
      className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${cls}`}
      title={`Answered by ${provider}`}
    >
      {provider}
    </span>
  );
}
