"use client";

import Link from "next/link";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/chat", label: "Chat" },
];

export function NavLinks() {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {LINKS.map(({ href, label }) => (
        <Link
          key={href}
          href={href}
          style={{
            padding: "5px 12px",
            borderRadius: 6,
            fontSize: 14,
            fontWeight: 500,
            color: "var(--text-muted)",
            textDecoration: "none",
            transition: "background 0.15s, color 0.15s",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = "var(--accent-light)";
            (e.currentTarget as HTMLElement).style.color = "var(--accent)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
            (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
          }}
        >
          {label}
        </Link>
      ))}
    </div>
  );
}
