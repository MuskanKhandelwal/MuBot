import type { Metadata } from "next";
import Link from "next/link";
import { NavLinks } from "@/components/NavLinks";
import "./globals.css";

export const metadata: Metadata = {
  title: "MuBot",
  description: "Your job search assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" style={{ height: "100%" }}>
      <body
        style={{
          minHeight: "100%",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "var(--bg)",
          color: "var(--text)",
        }}
      >
        {/* Nav */}
        <header
          style={{
            backgroundColor: "var(--surface)",
            borderBottom: "1px solid var(--border)",
            position: "sticky",
            top: 0,
            zIndex: 10,
            boxShadow: "0 1px 4px rgba(37,99,235,0.07)",
          }}
        >
          <nav
            style={{
              maxWidth: 1100,
              margin: "0 auto",
              padding: "0 24px",
              height: 56,
              display: "flex",
              alignItems: "center",
              gap: 32,
            }}
          >
            {/* Logo */}
            <Link
              href="/"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                textDecoration: "none",
                fontWeight: 700,
                fontSize: 17,
                color: "var(--accent)",
                letterSpacing: "-0.3px",
              }}
            >
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 28,
                  height: 28,
                  borderRadius: 8,
                  backgroundColor: "var(--accent)",
                  color: "#fff",
                  fontSize: 14,
                }}
              >
                M
              </span>
              MuBot
            </Link>

            {/* Links */}
            <NavLinks />
          </nav>
        </header>

        {/* Page content */}
        <main
          style={{
            flex: 1,
            maxWidth: 1100,
            width: "100%",
            margin: "0 auto",
            padding: "32px 24px",
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
