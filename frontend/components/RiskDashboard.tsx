"use client";

import { useEffect, useRef, useState } from "react";
import {
  getRiskFlags,
  runRiskDiff,
  setAsTemplate,
  type DocumentListItem,
  type RiskFlagItem,
} from "@/lib/api";
import { sortBySeverityDesc } from "@/lib/severity";
import RiskMarginRail from "@/components/RiskMarginRail";
import RiskFlagCard from "@/components/RiskFlagCard";

interface RiskDashboardProps {
  document: DocumentListItem;
}

export default function RiskDashboard({ document }: RiskDashboardProps) {
  const [flags, setFlags] = useState<RiskFlagItem[] | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    getRiskFlags(document.document_id)
      .then((data) => setFlags(sortBySeverityDesc(data)))
      .catch(() => setFlags([]));
  }, [document.document_id]);

  async function handleRunDiff() {
    setIsRunning(true);
    setError(null);
    try {
      const result = await runRiskDiff(document.document_id);
      setFlags(sortBySeverityDesc(result));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run the comparison.");
    } finally {
      setIsRunning(false);
    }
  }

  async function handleSetTemplate() {
    setError(null);
    try {
      await setAsTemplate(document.document_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not set as template.");
    }
  }

  function handleSelect(index: number) {
    setActiveIndex(index);
    cardRefs.current[index]?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-rule pb-4">
        <div>
          <h2 className="font-display text-lg font-semibold text-ink">{document.filename}</h2>
          <p className="text-sm text-muted">
            {document.contract_type || "No contract type set"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSetTemplate}
            className="rounded border border-rule px-3 py-1.5 text-sm text-ink hover:border-ink"
          >
            Use as template
          </button>
          <button
            onClick={handleRunDiff}
            disabled={isRunning}
            className="rounded bg-filed px-3 py-1.5 text-sm font-medium text-white hover:bg-filed/90 disabled:opacity-40"
          >
            {isRunning ? "Comparing…" : "Compare to template"}
          </button>
        </div>
      </div>

      {error && <p className="mb-4 text-sm text-flag-high">{error}</p>}

      {flags === null && <p className="text-sm text-muted">Loading…</p>}

      {flags !== null && flags.length === 0 && (
        <div className="rounded-lg border border-dashed border-rule p-8 text-center">
          <p className="text-sm text-ink">No deviations on record yet.</p>
          <p className="mt-1 text-sm text-muted">
            Run &ldquo;Compare to template&rdquo; to check this contract against your
            standard template, once one is set.
          </p>
        </div>
      )}

      {flags !== null && flags.length > 0 && (
        <div className="flex gap-4">
          <RiskMarginRail flags={flags} activeIndex={activeIndex} onSelect={handleSelect} />
          <div className="flex flex-1 flex-col gap-4">
            {flags.map((flag, i) => (
              <div key={i} ref={(el) => { cardRefs.current[i] = el; }}>
                <RiskFlagCard flag={flag} isActive={activeIndex === i} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
