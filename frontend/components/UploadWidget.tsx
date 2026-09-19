"use client";

import { useRef, useState } from "react";
import { uploadDocument } from "@/lib/api";

interface UploadWidgetProps {
  onUploaded: () => void;
}

export default function UploadWidget({ onUploaded }: UploadWidgetProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setError(null);
    setIsUploading(true);
    try {
      await uploadDocument(file);
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
          isDragging ? "border-filed bg-filed-soft" : "border-rule bg-surface"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />
        {isUploading ? (
          <p className="text-sm text-muted">Uploading…</p>
        ) : (
          <>
            <p className="text-sm font-medium text-ink">
              Drop a contract here, or click to browse
            </p>
            <p className="mt-1 text-xs text-muted">PDF, DOCX, or TXT — up to 25MB</p>
          </>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-flag-high">{error}</p>}
    </div>
  );
}
