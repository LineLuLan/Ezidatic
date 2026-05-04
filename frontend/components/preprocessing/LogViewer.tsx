import type { PipelineLog } from "@/lib/types";

export function LogViewer({ logs }: { logs: PipelineLog[] }) {
  if (logs.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No pipeline runs yet. Add steps and hit Run.
      </p>
    );
  }
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">When</th>
            <th className="px-3 py-2">Order</th>
            <th className="px-3 py-2">Step</th>
            <th className="px-3 py-2">Params</th>
            <th className="px-3 py-2">Applied changes</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {logs.map((row) => (
            <tr key={row.id} className="align-top">
              <td className="px-3 py-2 text-xs text-muted-foreground whitespace-nowrap">
                {new Date(row.created_at).toLocaleString()}
              </td>
              <td className="px-3 py-2 font-mono">{row.step_order}</td>
              <td className="px-3 py-2 font-medium">{row.step_name}</td>
              <td className="px-3 py-2">
                <pre className="max-w-xs overflow-x-auto whitespace-pre-wrap font-mono text-xs">
                  {row.params ? JSON.stringify(row.params, null, 2) : "—"}
                </pre>
              </td>
              <td className="px-3 py-2">
                <pre className="max-w-md overflow-x-auto whitespace-pre-wrap font-mono text-xs">
                  {row.applied_changes
                    ? JSON.stringify(row.applied_changes, null, 2)
                    : "—"}
                </pre>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
