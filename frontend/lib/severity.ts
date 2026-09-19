import type { RiskFlagItem } from "./api";

export type SeverityBand = "high" | "mid" | "low";

export function severityBand(severity: number): SeverityBand {
  if (severity >= 0.6) return "high";
  if (severity >= 0.3) return "mid";
  return "low";
}

export const SEVERITY_STYLES: Record<SeverityBand, { dot: string; text: string; bg: string; label: string }> = {
  high: { dot: "bg-flag-high", text: "text-flag-high", bg: "bg-flag-high-soft", label: "High risk" },
  mid: { dot: "bg-flag-mid", text: "text-flag-mid", bg: "bg-flag-mid-soft", label: "Worth reviewing" },
  low: { dot: "bg-muted", text: "text-muted", bg: "bg-paper", label: "Minor" },
};

export function sortBySeverityDesc(flags: RiskFlagItem[]): RiskFlagItem[] {
  return [...flags].sort((a, b) => b.severity - a.severity);
}
