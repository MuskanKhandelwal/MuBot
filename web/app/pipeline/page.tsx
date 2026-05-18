import { api, type PipelineRow } from "@/lib/api";

function formatDate(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function StatusPill({ status, replied }: { status: string; replied: boolean }) {
  let cls =
    "bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300";
  if (replied) {
    cls =
      "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200";
  } else if (status === "Overdue") {
    cls =
      "bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200";
  } else if (status === "All sent") {
    cls = "bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200";
  }
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}
    >
      {status}
    </span>
  );
}

export default async function PipelinePage() {
  let rows: PipelineRow[] = [];
  let error: string | null = null;

  try {
    rows = await api.pipeline();
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/30 p-6">
        <h2 className="font-semibold text-rose-700 dark:text-rose-300">
          Could not load pipeline
        </h2>
        <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">{error}</p>
      </div>
    );
  }

  const replied = rows.filter((r) => r.replied).length;
  const overdue = rows.filter((r) => r.status === "Overdue").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Pipeline</h1>
        <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
          {rows.length} outreach threads · {replied} replied · {overdue} overdue
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-neutral-50 dark:bg-neutral-950/40 border-b border-neutral-200 dark:border-neutral-800">
              <tr className="text-left text-xs uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Follow-ups</th>
                <th className="px-4 py-3 font-medium">Next due</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
              {rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-12 text-center text-neutral-500 dark:text-neutral-400"
                  >
                    No outreach threads yet.
                  </td>
                </tr>
              ) : (
                rows.map((r) => (
                  <tr
                    key={r.key}
                    className="hover:bg-neutral-50 dark:hover:bg-neutral-800/30"
                  >
                    <td className="px-4 py-3 font-medium">{r.company}</td>
                    <td className="px-4 py-3 text-neutral-600 dark:text-neutral-400">
                      {r.role}
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill status={r.status} replied={r.replied} />
                    </td>
                    <td className="px-4 py-3 tabular-nums text-neutral-600 dark:text-neutral-400">
                      {r.followups_sent}/{r.followups_total}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-neutral-600 dark:text-neutral-400">
                      {formatDate(r.next_due_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
