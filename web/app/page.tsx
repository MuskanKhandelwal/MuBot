import { api, type Status } from "@/lib/api";

type Tone = "default" | "warn" | "good" | "bad";

const toneColor: Record<Tone, string> = {
  default: "var(--text)",
  warn: "var(--warn)",
  good: "var(--good)",
  bad: "var(--bad)",
};

function StatCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: Tone;
}) {
  return (
    <div
      style={{
        backgroundColor: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 14,
        padding: "20px 22px",
        boxShadow: "0 2px 8px rgba(37,99,235,0.06)",
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          color: "var(--text-muted)",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 32,
          fontWeight: 700,
          fontVariantNumeric: "tabular-nums",
          lineHeight: 1.1,
          color: toneColor[tone],
        }}
      >
        {value}
      </div>
      {hint && (
        <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{hint}</div>
      )}
    </div>
  );
}

function formatLastRun(value: string | null): string {
  if (!value) return "never";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default async function DashboardPage() {
  let status: Status | null = null;
  let error: string | null = null;

  try {
    status = await api.status();
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error || !status) {
    return (
      <div
        style={{
          backgroundColor: "#fef2f2",
          border: "1px solid #fecaca",
          borderRadius: 14,
          padding: 24,
        }}
      >
        <div style={{ fontWeight: 600, color: "#dc2626", marginBottom: 6 }}>
          Could not load status
        </div>
        <div style={{ fontSize: 14, color: "#b91c1c" }}>{error ?? "No data"}</div>
        <div style={{ fontSize: 12, color: "#b91c1c", marginTop: 12 }}>
          Is the API running?{" "}
          <code
            style={{
              fontFamily: "var(--font-mono, monospace)",
              backgroundColor: "#fee2e2",
              padding: "1px 5px",
              borderRadius: 4,
            }}
          >
            uvicorn api.main:app --reload
          </code>
        </div>
      </div>
    );
  }

  const replyRatePct = Math.round(status.reply_rate * 100);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <h1
            style={{
              fontSize: 24,
              fontWeight: 700,
              letterSpacing: "-0.4px",
              margin: 0,
              color: "var(--text)",
            }}
          >
            Dashboard
          </h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--text-muted)" }}>
            Last heartbeat: {formatLastRun(status.last_run)}
          </p>
        </div>

        {status.campaigns_paused ? (
          <span
            style={{
              backgroundColor: "#fef3c7",
              color: "#92400e",
              border: "1px solid #fde68a",
              borderRadius: 99,
              padding: "4px 12px",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            ⚠ Paused{status.pause_reason ? `: ${status.pause_reason}` : ""}
          </span>
        ) : (
          <span
            style={{
              backgroundColor: "#dcfce7",
              color: "#166534",
              border: "1px solid #bbf7d0",
              borderRadius: 99,
              padding: "4px 12px",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            ● Active
          </span>
        )}
      </div>

      {/* Main stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16,
        }}
      >
        <StatCard
          label="Sent today"
          value={status.daily_email_count}
          hint="initial + follow-ups"
        />
        <StatCard
          label="Pending follow-ups"
          value={status.pending_followups}
          hint="scheduled, not yet sent"
        />
        <StatCard
          label="Overdue"
          value={status.overdue_followups}
          tone={status.overdue_followups > 0 ? "warn" : "default"}
          hint="past due date"
        />
        <StatCard
          label="Reply rate"
          value={`${replyRatePct}%`}
          tone={replyRatePct >= 20 ? "good" : "default"}
          hint={`${status.positives}/${status.total_tracked} tracked`}
        />
      </div>

      {/* Divider */}
      <div style={{ borderTop: "1px solid var(--border)" }} />

      {/* Reply outcomes */}
      <div>
        <h2
          style={{
            fontSize: 15,
            fontWeight: 600,
            margin: "0 0 16px",
            color: "var(--text)",
          }}
        >
          Reply outcomes
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 16,
          }}
        >
          <StatCard label="Positives" value={status.positives} tone="good" />
          <StatCard label="Rejections" value={status.rejections} tone="bad" />
          <StatCard label="No response" value={status.no_responses} />
        </div>
      </div>
    </div>
  );
}
