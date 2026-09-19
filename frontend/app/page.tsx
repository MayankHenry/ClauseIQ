"use client";

import { useState } from "react";
import UploadWidget from "@/components/UploadWidget";
import DocumentList from "@/components/DocumentList";

export default function HomePage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="flex flex-col gap-10">
      <div>
        <p className="mb-1 font-mono text-xs uppercase tracking-widest text-muted">
          Intake
        </p>
        <h1 className="font-display text-xl font-semibold text-ink">Upload a contract</h1>
        <p className="mt-1 text-sm text-muted">
          PDF, DOCX, or TXT. Once processed, ask questions grounded in exact clause
          citations, or compare it against your standard template.
        </p>
        <div className="mt-4">
          <UploadWidget onUploaded={() => setRefreshKey((k) => k + 1)} />
        </div>
      </div>

      <div>
        <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted">
          Your documents
        </h2>
        <DocumentList refreshKey={refreshKey} />
      </div>
    </div>
  );
}
