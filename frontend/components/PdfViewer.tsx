"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";

export interface PdfViewerHandle {
  goToPage: (pageNumber: number) => void;
}

interface PdfViewerProps {
  fileUrl: string;
}

/**
 * Renders a PDF using pdfjs-dist, one page at a time, with a page-jump
 * method exposed via ref so a citation click elsewhere on the page can
 * navigate the viewer directly to the cited clause's page.
 *
 * Known limitation: this jumps to the correct PAGE, not the exact clause
 * bounding box -- clause-level bbox coordinates aren't captured by the
 * ingestion pipeline yet (Clause.bbox exists in the schema but is
 * currently always null), so pixel-perfect in-page highlighting isn't
 * possible with the data available today. Page-level navigation is an
 * honest, fully-functional step toward that, and a natural next
 * enhancement once bbox extraction is added to the chunker.
 */
const PdfViewer = forwardRef<PdfViewerHandle, PdfViewerProps>(function PdfViewer(
  { fileUrl },
  ref
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pdfDocRef = useRef<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [flashPage, setFlashPage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const pdfjsLib = await import("pdfjs-dist");
        pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

        const loadingTask = pdfjsLib.getDocument(fileUrl);
        const pdf = await loadingTask.promise;
        if (cancelled) return;

        pdfDocRef.current = pdf;
        setNumPages(pdf.numPages);
        renderPage(1);
      } catch (err) {
        if (!cancelled) {
          setError("Could not load PDF preview.");
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileUrl]);

  async function renderPage(pageNumber: number) {
    const pdf = pdfDocRef.current;
    const canvas = canvasRef.current;
    if (!pdf || !canvas) return;

    const page = await pdf.getPage(pageNumber);
    const viewport = page.getViewport({ scale: 1.3 });
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    const context = canvas.getContext("2d");
    if (!context) return;

    await page.render({ canvasContext: context, viewport }).promise;
    setCurrentPage(pageNumber);
  }

  useImperativeHandle(ref, () => ({
    goToPage: (pageNumber: number) => {
      renderPage(pageNumber);
      setFlashPage(true);
      setTimeout(() => setFlashPage(false), 900);
    },
  }));

  if (error) {
    return <p className="text-sm text-flag-high">{error}</p>;
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`overflow-auto rounded-lg border transition-shadow ${
          flashPage ? "ring-4 ring-filed" : "border-rule"
        }`}
      >
        <canvas ref={canvasRef} />
      </div>
      {numPages && (
        <div className="flex items-center gap-3 text-sm text-muted">
          <button
            className="rounded border border-rule px-2 py-1 disabled:opacity-40"
            onClick={() => renderPage(Math.max(1, currentPage - 1))}
            disabled={currentPage <= 1}
          >
            Prev
          </button>
          <span>
            Page {currentPage} of {numPages}
          </span>
          <button
            className="rounded border border-rule px-2 py-1 disabled:opacity-40"
            onClick={() => renderPage(Math.min(numPages, currentPage + 1))}
            disabled={currentPage >= numPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
});

export default PdfViewer;
