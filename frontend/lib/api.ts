/**
 * Typed client for the ClauseIQ FastAPI backend. Centralizes the base
 * URL and response typing so pages/components don't hand-roll fetch
 * calls and drift out of sync with the API schema.
 */

import { authHeaders } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type DocumentStatus = "uploaded" | "parsing" | "ready" | "failed";

export interface DocumentListItem {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  contract_type: string | null;
}

export interface DocumentStatusResponse {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  contract_type: string | null;
  clause_count: number | null;
}

export interface CitedClause {
  clause_id: string;
  document_id: string;
  section_number: string | null;
  clause_type: string | null;
  page: number | null;
  text: string;
}

export interface QueryResponse {
  query_id: string;
  answer: string;
  grounded: boolean;
  cited_clauses: CitedClause[];
}

export interface RiskFlagItem {
  clause_id: string | null;
  clause_type: string | null;
  flag_type: string | null;
  severity: number;
  description: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ? JSON.stringify(body.detail) : detail;
    } catch {
      // response wasn't JSON -- fall back to statusText
    }
    throw new Error(`API error (${res.status}): ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function login(password: string): Promise<{ access_token: string }> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  return handleResponse(res);
}

export async function uploadDocument(
  file: File,
  contractType?: string
): Promise<{ document_id: string; filename: string; status: string }> {
  const form = new FormData();
  form.append("file", file);
  if (contractType) form.append("contract_type", contractType);

  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  return handleResponse(res);
}

export async function listDocuments(): Promise<DocumentListItem[]> {
  const res = await fetch(`${API_BASE_URL}/documents`);
  return handleResponse(res);
}

export async function getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/status`);
  return handleResponse(res);
}

export async function askQuestion(
  question: string,
  documentIds?: string[]
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      document_ids: documentIds && documentIds.length > 0 ? documentIds : null,
    }),
  });
  return handleResponse(res);
}

export async function setAsTemplate(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/set-template`, {
    method: "POST",
    headers: authHeaders(),
  });
  await handleResponse(res);
}

export async function runRiskDiff(documentId: string): Promise<RiskFlagItem[]> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/risk-diff`, {
    method: "POST",
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function getRiskFlags(documentId: string): Promise<RiskFlagItem[]> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/risk-flags`);
  return handleResponse(res);
}
