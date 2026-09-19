"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listDocuments, type DocumentListItem } from "@/lib/api";

export default function RiskPickerPage() {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);

  useEffect(() => {
    listDocuments().then((docs) => setDocuments(docs.filter((d) => d.status === "ready")));
  }, []);

  return (
    <div>
      <h1 className="mb-1 font-display text-xl font-semibold text-ink">Risk review</h1>
      <p className="mb-6 text-sm text-muted">
        Pick a document to compare against your standard template for its contract type.
      </p>

      {documents.length === 0 ? (
        <p className="text-sm text-muted">No ready documents yet. Upload one first.</p>
      ) : (
        <ul className="divide-y divide-rule rounded-lg border border-rule bg-surface">
          {documents.map((doc) => (
            <li key={doc.document_id}>
              <Link
                href={`/risk/${doc.document_id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-paper"
              >
                <div>
                  <p className="text-sm font-medium text-ink">{doc.filename}</p>
                  <p className="text-xs text-muted">
                    {doc.contract_type || "No contract type set"}
                  </p>
                </div>
                <span className="font-mono text-xs text-muted">review →</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
