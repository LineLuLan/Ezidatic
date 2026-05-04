import type { ColumnProfile } from "@/lib/types";

function formatStat(value: number | undefined): string {
  if (value === undefined || value === null) return "-";
  if (Math.abs(value) >= 1000 || (Math.abs(value) > 0 && Math.abs(value) < 0.01)) {
    return value.toExponential(2);
  }
  return value.toFixed(2);
}

interface ColumnTableProps {
  columns: ColumnProfile[];
  onSelect?: (column: ColumnProfile) => void;
  selectedName?: string | null;
}

export function ColumnTable({ columns, onSelect, selectedName }: ColumnTableProps) {
  const isClickable = !!onSelect;
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Column</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2 text-right">Nulls</th>
            <th className="px-3 py-2 text-right">Unique</th>
            <th className="px-3 py-2 text-right">Min</th>
            <th className="px-3 py-2 text-right">Max</th>
            <th className="px-3 py-2 text-right">Mean</th>
            <th className="px-3 py-2 text-right">Std</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {columns.map((c) => {
            const isSelected = selectedName === c.name;
            return (
              <tr
                key={c.name}
                onClick={isClickable ? () => onSelect!(c) : undefined}
                className={[
                  "hover:bg-accent/50",
                  isClickable ? "cursor-pointer" : "",
                  isSelected ? "bg-accent" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <td className="px-3 py-2 font-medium">{c.name}</td>
                <td className="px-3 py-2 text-muted-foreground">{c.dtype}</td>
                <td className="px-3 py-2 text-right">{c.null_count}</td>
                <td className="px-3 py-2 text-right">{c.unique_count}</td>
                <td className="px-3 py-2 text-right">{formatStat(c.stats?.min)}</td>
                <td className="px-3 py-2 text-right">{formatStat(c.stats?.max)}</td>
                <td className="px-3 py-2 text-right">{formatStat(c.stats?.mean)}</td>
                <td className="px-3 py-2 text-right">{formatStat(c.stats?.std)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
