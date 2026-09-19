import type { DocumentStatus } from "@/lib/api";

const STATUS_STYLES: Record<DocumentStatus, string> = {
  uploaded: "bg-paper text-muted",
  parsing: "bg-flag-mid-soft text-flag-mid",
  ready: "bg-flag-clear-soft text-flag-clear",
  failed: "bg-flag-high-soft text-flag-high",
};

const STATUS_LABELS: Record<DocumentStatus, string> = {
  uploaded: "Uploaded",
  parsing: "Processing…",
  ready: "Ready",
  failed: "Failed",
};

export default function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-mono text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {status === "parsing" && (
        <span className="mr-1.5 h-1.5 w-1.5 animate-pulse rounded-full bg-flag-mid" />
      )}
      {STATUS_LABELS[status]}
    </span>
  );
}
