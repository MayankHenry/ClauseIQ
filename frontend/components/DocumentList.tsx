"use client";

import { useEffect, useRef, useState } from "react";
import { listDocuments, type DocumentListItem } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";

const POLL_INTERVAL_MS = 3000;

export default function DocumentList({ refreshKey }: { refreshKey: number }) {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function fetchDocuments() {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load documents.");
    }
  }

  useEffect(() => {
    fetchDocuments();
  }, [refreshKey]);

  // Poll only while at least one document is still being processed --
  // avoids hammering the API once everything has settled into ready/failed.
  useEffect(() => {
    const hasInFlight = documents.some((d) => d.status === "uploaded" || d.status === "parsing");

    if (hasInFlight && !intervalRef.current) {
      intervalRef.current = setInterval(fetchDocuments, POLL_INTERVAL_MS);
    } else if (!hasInFlight && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [documents]);

  if (error) {
    return <p className="text-sm text-flag-high">{error}</p>;
  }

  if (documents.length === 0) {
    return <p className="text-sm text-muted">No documents uploaded yet.</p>;
  }

  return (
    <ul className="divide-y divide-rule rounded-lg border border-rule bg-surface">
      {documents.map((doc) => (
        <li key={doc.document_id} className="flex items-center justify-between px-4 py-3">
          <div>
            <p className="text-sm font-medium text-ink">{doc.filename}</p>
            {doc.contract_type && (
              <p className="text-xs text-muted">{doc.contract_type}</p>
            )}
          </div>
          <StatusBadge status={doc.status} />
        </li>
      ))}
    </ul>
  );
}
