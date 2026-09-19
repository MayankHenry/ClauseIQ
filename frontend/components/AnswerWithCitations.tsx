import type { CitedClause } from "@/lib/api";

interface AnswerWithCitationsProps {
  answer: string;
  citedClauses: CitedClause[];
  onCitationClick: (clause: CitedClause) => void;
}

const CITATION_REGEX = /\[clause:([a-zA-Z0-9-]+)\]/g;

/**
 * Splits the raw answer text on [clause:ID] markers and renders each one
 * as a clickable numbered citation button, backed by the actual cited
 * clause data returned alongside the answer.
 */
export default function AnswerWithCitations({
  answer,
  citedClauses,
  onCitationClick,
}: AnswerWithCitationsProps) {
  const clauseById = new Map(citedClauses.map((c) => [c.clause_id, c]));

  const parts: (string | { clauseId: string })[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  CITATION_REGEX.lastIndex = 0;
  while ((match = CITATION_REGEX.exec(answer)) !== null) {
    if (match.index > lastIndex) {
      parts.push(answer.slice(lastIndex, match.index));
    }
    parts.push({ clauseId: match[1] });
    lastIndex = CITATION_REGEX.lastIndex;
  }
  if (lastIndex < answer.length) {
    parts.push(answer.slice(lastIndex));
  }

  return (
    <p className="text-sm leading-relaxed text-ink">
      {parts.map((part, i) => {
        if (typeof part === "string") {
          return <span key={i}>{part}</span>;
        }
        const clause = clauseById.get(part.clauseId);
        if (!clause) {
          // citation referenced a clause not in the cited_clauses list --
          // shouldn't happen given the backend guardrail, but render
          // plainly rather than crash if it ever does
          return <span key={i} className="text-muted">[source]</span>;
        }
        return (
          <button
            key={i}
            onClick={() => onCitationClick(clause)}
            className="mx-0.5 inline-flex items-center rounded bg-filed/10 px-1.5 py-0.5 text-xs font-medium text-filed hover:bg-filed/20"
            title={clause.text.slice(0, 100)}
          >
            {clause.section_number ? `§${clause.section_number}` : "source"}
          </button>
        );
      })}
    </p>
  );
}
