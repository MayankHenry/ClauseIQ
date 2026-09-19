"use client";

import { useEffect, useRef, useState } from "react";
import {
  askQuestion,
  listDocuments,
  type CitedClause,
  type DocumentListItem,
  type QueryResponse,
} from "@/lib/api";
import AnswerWithCitations from "@/components/AnswerWithCitations";
import ClauseSourcePanel from "@/components/ClauseSourcePanel";
import PdfViewer, { type PdfViewerHandle } from "@/components/PdfViewer";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ChatInterface() {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [activeClause, setActiveClause] = useState<CitedClause | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pdfViewerRef = useRef<PdfViewerHandle>(null);

  useEffect(() => {
    listDocuments().then((docs) => {
      setDocuments(docs.filter((d) => d.status === "ready"));
    });
  }, []);

  const selectedDoc = documents.find((d) => d.document_id === selectedDocId);
  const isSelectedDocPdf = selectedDoc?.filename.toLowerCase().endsWith(".pdf");

  async function handleAsk() {
    if (!question.trim()) return;
    setIsAsking(true);
    setError(null);
    setActiveClause(null);
    try {
      const result = await askQuestion(question, selectedDocId ? [selectedDocId] : undefined);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsAsking(false);
    }
  }

  function handleCitationClick(clause: CitedClause) {
    setActiveClause(clause);
    if (isSelectedDocPdf && clause.page && pdfViewerRef.current) {
      pdfViewerRef.current.goToPage(clause.page);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="flex flex-col gap-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted">
            Search within (optional)
          </label>
          <select
            value={selectedDocId}
            onChange={(e) => {
              setSelectedDocId(e.target.value);
              setActiveClause(null);
            }}
            className="w-full rounded border border-rule px-3 py-2 text-sm"
          >
            <option value="">All documents</option>
            {documents.map((d) => (
              <option key={d.document_id} value={d.document_id}>
                {d.filename}
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder="e.g. What happens if we want to end this contract early?"
            className="flex-1 rounded border border-rule px-3 py-2 text-sm"
          />
          <button
            onClick={handleAsk}
            disabled={isAsking || !question.trim()}
            className="rounded bg-filed px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {isAsking ? "Asking…" : "Ask"}
          </button>
        </div>

        {error && <p className="text-sm text-flag-high">{error}</p>}

        {response && (
          <div className="rounded-lg border border-rule bg-surface p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                Answer
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  response.grounded
                    ? "bg-green-100 text-green-700"
                    : "bg-amber-100 text-amber-700"
                }`}
              >
                {response.grounded ? "Grounded in source clauses" : "Not confidently grounded"}
              </span>
            </div>
            <AnswerWithCitations
              answer={response.answer}
              citedClauses={response.cited_clauses}
              onCitationClick={handleCitationClick}
            />
          </div>
        )}

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
            Source clause
          </h3>
          <ClauseSourcePanel clause={activeClause} />
        </div>
      </div>

      <div>
        {isSelectedDocPdf ? (
          <PdfViewer
            ref={pdfViewerRef}
            fileUrl={`${API_BASE_URL}/documents/${selectedDocId}/file`}
          />
        ) : (
          <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-rule p-10 text-center text-sm text-muted">
            {selectedDoc
              ? "PDF preview is only available for .pdf uploads. Use the source clause panel to see the cited text."
              : "Select a single document to enable the PDF preview and page-jump on citation click."}
          </div>
        )}
      </div>
    </div>
  );
}
