"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login as loginRequest } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const { access_token } = await loginRequest(password);
      setToken(access_token);
      router.replace("/");
    } catch {
      setError("That password didn't work. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm">
        <p className="mb-1 font-mono text-xs uppercase tracking-widest text-muted">
          Restricted access
        </p>
        <h1 className="mb-6 font-display text-2xl font-semibold text-ink">
          Enter the review room
        </h1>

        <label className="mb-1 block text-sm font-medium text-ink" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border border-rule bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-filed"
        />

        {error && <p className="mt-2 text-sm text-flag-high">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting || !password}
          className="mt-4 w-full rounded bg-filed px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-filed/90 disabled:opacity-40"
        >
          {isSubmitting ? "Checking…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
