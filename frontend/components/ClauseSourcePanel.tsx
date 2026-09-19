import type { CitedClause } from "@/lib/api";

interface ClauseSourcePanelProps {
  clause: CitedClause | null;
}

export default function ClauseSourcePanel({ clause }: ClauseSourcePanelProps) {
  if (!clause) {
    return (
      <div className="rounded-lg border border-dashed border-rule p-6 text-center text-sm text-muted">
        Click a citation in the answer to see its source clause here.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-filed/30 bg-filed-soft p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted">
        {clause.section_number && (
          <span className="rounded bg-surface px-2 py-0.5 font-medium text-ink">
            Section {clause.section_number}
          </span>
        )}
        {clause.clause_type && (
          <span className="rounded bg-surface px-2 py-0.5 font-medium text-ink">
            {clause.clause_type.replace(/_/g, " ")}
          </span>
        )}
        {clause.page && (
          <span className="rounded bg-surface px-2 py-0.5 font-medium text-ink">
            Page {clause.page}
          </span>
        )}
      </div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{clause.text}</p>
    </div>
  );
}
