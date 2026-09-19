import type { RiskFlagItem } from "@/lib/api";
import { severityBand, SEVERITY_STYLES } from "@/lib/severity";

interface RiskFlagCardProps {
  flag: RiskFlagItem;
  isActive: boolean;
}

export default function RiskFlagCard({ flag, isActive }: RiskFlagCardProps) {
  const band = severityBand(flag.severity);
  const style = SEVERITY_STYLES[band];

  return (
    <div
      className={`rounded-lg border bg-surface p-4 transition-shadow ${
        isActive ? "border-ink shadow-sm" : "border-rule"
      }`}
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs uppercase tracking-wide text-muted">
          {flag.clause_type?.replace(/_/g, " ") || "clause"}
        </span>
        <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}>
          {flag.flag_type === "missing" ? "Missing from contract" : style.label}
        </span>
        <span className="ml-auto font-mono text-xs text-muted">
          severity {flag.severity.toFixed(1)}
        </span>
      </div>
      <p className="text-sm leading-relaxed text-ink">{flag.description}</p>
    </div>
  );
}
