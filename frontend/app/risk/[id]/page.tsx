"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { listDocuments, type DocumentListItem } from "@/lib/api";
import RiskDashboard from "@/components/RiskDashboard";

export default function RiskDetailPage() {
  const params = useParams();
  const documentId = params.id as string;
  const [document, setDocument] = useState<DocumentListItem | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    listDocuments().then((docs) => {
      const found = docs.find((d) => d.document_id === documentId);
      if (found) {
        setDocument(found);
      } else {
        setNotFound(true);
      }
    });
  }, [documentId]);

  if (notFound) {
    return <p className="text-sm text-muted">Document not found.</p>;
  }

  if (!document) {
    return <p className="text-sm text-muted">Loading…</p>;
  }

  return <RiskDashboard document={document} />;
}
