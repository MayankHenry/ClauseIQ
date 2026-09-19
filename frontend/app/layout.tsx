import "./globals.css";
import type { ReactNode } from "react";
import { sourceSerif, plexSans, plexMono } from "./fonts";
import AuthGate from "@/components/AuthGate";

export const metadata = {
  title: "ClauseIQ",
  description: "Contract review, grounded in exact clause citations.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sourceSerif.variable} ${plexSans.variable} ${plexMono.variable}`}>
      <body className="min-h-screen font-sans">
        <header className="border-b border-rule bg-surface px-6 py-4">
          <div className="mx-auto flex max-w-3xl items-center justify-between">
            <a href="/" className="font-display text-lg font-semibold tracking-tight text-ink">
              ClauseIQ
            </a>
            <nav className="flex items-center gap-6 text-sm text-muted">
              <a href="/" className="hover:text-ink">
                Documents
              </a>
              <a href="/chat" className="hover:text-ink">
                Ask
              </a>
              <a href="/risk" className="hover:text-ink">
                Risk review
              </a>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-3xl px-6 py-10">
          <AuthGate>{children}</AuthGate>
        </main>
      </body>
    </html>
  );
}
