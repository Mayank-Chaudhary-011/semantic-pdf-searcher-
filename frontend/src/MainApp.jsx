import React, { useState, useRef, useEffect, useCallback } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { supabase } from "./lib/supabaseClient";
import {
  LogOut,
  Search,
  FileText,
  ChevronRight,
  Sparkles,
  X,
  Trash2,
  Library,
  FolderOpen,
  ChevronLeft,
} from "lucide-react";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const MAX_PAGE_WIDTH = 820;
const PAGE_PADDING = 48;

async function authHeaders() {
  let {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    const { data: refreshed } = await supabase.auth.refreshSession();
    session = refreshed?.session ?? null;
  }
  if (!session?.access_token) throw new Error("NOT_LOGGED_IN");
  return { Authorization: `Bearer ${session.access_token}` };
}

const T = {
  cream: "#F5F0E8",
  ink: "#1A1714",
  inkMid: "#4A443E",
  inkFaint: "#9B938A",
  amber: "#C4830A",
  amberBg: "#FEF3DC",
  border: "#E2D9CE",
  borderMid: "#CFC5BA",
  white: "#FFFFFF",
  sidebarBg: "#EDE8DF",
  cardHover: "#E8E1D6",
  cardActive: "#FEF3DC",
  danger: "#C0392B",
  dangerBg: "rgba(192,57,43,0.07)",
  dangerBorder: "rgba(192,57,43,0.2)",
};

const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: ${T.cream}; color: ${T.ink}; font-family: 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: ${T.borderMid}; border-radius: 99px; }
  ::-webkit-scrollbar-thumb:hover { background: ${T.inkFaint}; }
  .result-card { border: 1px solid ${T.border}; border-radius: 8px; padding: 12px 14px; cursor: pointer; background: ${T.white}; transition: background 0.15s, border-color 0.15s, box-shadow 0.15s; border-left: 3px solid transparent; }
  .result-card:hover { background: ${T.cardHover}; border-color: ${T.borderMid}; box-shadow: 0 1px 6px rgba(26,23,20,0.06); }
  .result-card.active { background: ${T.cardActive}; border-color: ${T.border}; border-left-color: ${T.amber}; box-shadow: 0 1px 8px rgba(196,131,10,0.1); }
  .pdf-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; border: 1px solid ${T.border}; background: ${T.white}; transition: background 0.15s, border-color 0.15s; }
  .pdf-item:hover { background: ${T.cardHover}; border-color: ${T.borderMid}; }
  .delete-btn { background: none; border: none; cursor: pointer; color: ${T.inkFaint}; display: flex; align-items: center; padding: 4px; border-radius: 5px; transition: color 0.15s, background 0.15s; flex-shrink: 0; }
  .delete-btn:hover { color: ${T.danger}; background: ${T.dangerBg}; }
  @keyframes shimmer { 0% { background-position: -400px 0; } 100% { background-position: 400px 0; } }
  .skeleton { border-radius: 4px; background: linear-gradient(90deg, ${T.border} 25%, ${T.cardHover} 50%, ${T.border} 75%); background-size: 800px 100%; animation: shimmer 1.4s ease-in-out infinite; }
  .highlight-box { position: absolute; pointer-events: none; border-radius: 2px; background: rgba(196,131,10,0.22); border: 1.5px solid rgba(196,131,10,0.55); }
  .progress-track { flex: 1; height: 4px; background: ${T.border}; border-radius: 99px; overflow: hidden; }
  .progress-fill { height: 100%; background: ${T.amber}; border-radius: 99px; transition: width 0.4s ease; }
  .btn-primary { background: ${T.ink}; color: ${T.white}; border: none; border-radius: 7px; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s, opacity 0.15s; letter-spacing: 0.01em; }
  .btn-primary:hover:not(:disabled) { background: #2E2925; }
  .btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-ghost { background: none; color: ${T.inkMid}; border: 1px solid ${T.border}; border-radius: 7px; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; cursor: pointer; transition: background 0.15s, color 0.15s, border-color 0.15s; }
  .btn-ghost:hover { background: ${T.border}; color: ${T.ink}; border-color: ${T.borderMid}; }
  .search-container:focus-within { border-color: ${T.amber} !important; box-shadow: 0 0 0 3px rgba(196,131,10,0.12) !important; }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
  .fade-up { animation: fadeUp 0.22s ease forwards; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes slideIn { from { transform: translateX(-100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
  @keyframes slideUp { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  .slide-up { animation: slideUp 0.28s cubic-bezier(0.22,1,0.36,1) forwards; }
  @media (max-width: 767px) {
    .desktop-only { display: none !important; }
    .header-email { display: none !important; }
    .header-actions { gap: 5px !important; }
    .header-actions .btn-ghost, .header-actions .btn-primary { padding: 5px 8px !important; font-size: 11px !important; }
  }
  @media (min-width: 768px) { .mobile-only { display: none !important; } }
`;

function useWindowWidth() {
  const [width, setWidth] = useState(
    typeof window !== "undefined" ? window.innerWidth : 1200,
  );
  useEffect(() => {
    const handler = () => setWidth(window.innerWidth);
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);
  return width;
}

function useViewerWidth() {
  const [width, setWidth] = useState(0);
  const [element, setElement] = useState(null);
  const refCallback = useCallback((node) => {
    if (node !== null) setElement(node);
  }, []);
  useEffect(() => {
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      setWidth(Math.min(MAX_PAGE_WIDTH, Math.max(320, w - PAGE_PADDING)));
    });
    observer.observe(element);
    setWidth(
      Math.min(
        MAX_PAGE_WIDTH,
        Math.max(320, element.clientWidth - PAGE_PADDING),
      ),
    );
    return () => observer.disconnect();
  }, [element]);
  return [width, refCallback];
}

function SkeletonCard() {
  return (
    <div
      style={{
        border: `1px solid ${T.border}`,
        borderRadius: 8,
        padding: "12px 14px",
        background: T.white,
      }}
    >
      <div
        className="skeleton"
        style={{ height: 9, width: "50%", marginBottom: 10 }}
      />
      <div
        className="skeleton"
        style={{ height: 8, width: "100%", marginBottom: 6 }}
      />
      <div
        className="skeleton"
        style={{ height: 8, width: "80%", marginBottom: 6 }}
      />
      <div className="skeleton" style={{ height: 8, width: "60%" }} />
    </div>
  );
}

function EmptyState({ icon: Icon, title, subtitle }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 10,
        padding: "48px 24px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 11,
          background: T.cream,
          border: `1px solid ${T.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 4,
        }}
      >
        <Icon size={18} color={T.inkFaint} />
      </div>
      <p style={{ fontSize: 13, fontWeight: 600, color: T.inkMid }}>{title}</p>
      {subtitle && (
        <p
          style={{
            fontSize: 12,
            color: T.inkFaint,
            maxWidth: 210,
            lineHeight: 1.6,
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}

function ScorePill({ score }) {
  const pct =
    score > 1
      ? Math.round(Math.min(score / 20, 1) * 100)
      : Math.round(score * 100);
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 600,
        fontFamily: "'JetBrains Mono', monospace",
        padding: "2px 6px",
        borderRadius: 99,
        background: T.amberBg,
        color: T.amber,
        border: `1px solid rgba(196,131,10,0.25)`,
      }}
    >
      {pct}%
    </span>
  );
}

// ── PDF Viewer panel — defined OUTSIDE MainApp to avoid React error #185 ──────
function PDFViewerContent({
  isMobile,
  setMobileView,
  selectedResult,
  pdfBlobUrl,
  pageWidth,
  numPages,
  pageDimensions,
  loadedPdfId,
  activeBoxes,
  viewerRef,
  viewerWidthRef,
  pageRefs,
  handlePageLoadSuccess,
}) {
  return (
    <>
      <div
        style={{
          height: 46,
          flexShrink: 0,
          borderBottom: `1px solid ${T.border}`,
          background: T.white,
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          gap: 8,
        }}
      >
        {isMobile && (
          <button
            onClick={() => setMobileView("results")}
            className="btn-ghost mobile-only"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              padding: "4px 8px",
              marginRight: 4,
            }}
          >
            <ChevronLeft size={14} /> Results
          </button>
        )}
        {selectedResult ? (
          <>
            <FileText size={12} color={T.amber} />
            <span
              style={{
                fontSize: 12,
                color: T.inkMid,
                fontWeight: 500,
                flex: 1,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {selectedResult.original_filename}
            </span>
            <span
              style={{
                fontSize: 10,
                color: T.inkFaint,
                padding: "2px 7px",
                borderRadius: 99,
                background: T.sidebarBg,
                border: `1px solid ${T.border}`,
                fontFamily: "'JetBrains Mono', monospace",
                flexShrink: 0,
              }}
            >
              p. {selectedResult.page_number}
            </span>
          </>
        ) : (
          <span style={{ fontSize: 12, color: T.inkFaint }}>
            Select a result to view the document
          </span>
        )}
      </div>

      <div
        ref={(node) => {
          viewerRef.current = node;
          viewerWidthRef(node);
        }}
        style={{
          flex: 1,
          minHeight: 0,
          minWidth: 0,
          overflowY: "auto",
          overflowX: "auto",
          background: T.cream,
          padding: "24px 24px 48px",
        }}
      >
        {!selectedResult && (
          <div
            style={{
              minHeight: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <EmptyState
              icon={FileText}
              title="Open a document"
              subtitle="Click any search result on the left to load the document and jump to the matching passage."
            />
          </div>
        )}
        {selectedResult && !pdfBlobUrl && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginTop: 80,
              justifyContent: "center",
            }}
          >
            <div
              style={{
                width: 20,
                height: 20,
                border: `2px solid ${T.border}`,
                borderTopColor: T.amber,
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }}
            />
            <span style={{ fontSize: 12, color: T.inkFaint }}>
              Loading document…
            </span>
          </div>
        )}
        {pdfBlobUrl && pageWidth > 0 && (
          <Document
            file={pdfBlobUrl}
            onLoadSuccess={({ numPages: n }) => numPages !== n && null}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 12,
              }}
            >
              {Array.from({ length: numPages || 0 }, (_, i) => i + 1).map(
                (pageNum) => {
                  const dims = pageDimensions[pageNum];
                  const isTargetPage =
                    selectedResult?.page_number === pageNum &&
                    selectedResult?.pdf_id === loadedPdfId;
                  const boxesToShow = isTargetPage ? activeBoxes : [];
                  return (
                    <div
                      key={pageNum}
                      ref={(el) => (pageRefs.current[pageNum] = el)}
                      style={{
                        position: "relative",
                        borderRadius: 6,
                        overflow: "hidden",
                        boxShadow: isTargetPage
                          ? `0 0 0 2px ${T.amber}, 0 4px 20px rgba(26,23,20,0.12)`
                          : "0 2px 12px rgba(26,23,20,0.08)",
                        transition: "box-shadow 0.25s",
                      }}
                    >
                      <Page
                        pageNumber={pageNum}
                        width={pageWidth}
                        renderTextLayer={true}
                        renderAnnotationLayer={true}
                        onLoadSuccess={(page) =>
                          handlePageLoadSuccess(pageNum, page)
                        }
                      />
                      {dims &&
                        boxesToShow.map((box, idx) => {
                          const scale = pageWidth / dims.width;
                          return (
                            <div
                              key={idx}
                              className="highlight-box"
                              style={{
                                left: box.x0 * scale,
                                top: box.y0 * scale,
                                width: (box.x1 - box.x0) * scale,
                                height: (box.y1 - box.y0) * scale,
                              }}
                            />
                          );
                        })}
                    </div>
                  );
                },
              )}
            </div>
          </Document>
        )}
      </div>
    </>
  );
}

export default function MainApp({ user, onSignOut }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageDimensions, setPageDimensions] = useState({});
  const [loadedPdfId, setLoadedPdfId] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [appError, setAppError] = useState(null);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [myPdfs, setMyPdfs] = useState([]);
  const [pdfsLoading, setPdfsLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [mobileView, setMobileView] = useState("results");

  const windowWidth = useWindowWidth();
  const isMobile = windowWidth < 768;

  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  const pageRefs = useRef({});
  const viewerRef = useRef(null);
  const isScrolling = useRef(false);

  const [pageWidth, viewerWidthRef] = useViewerWidth();
  const activeBoxes = React.useMemo(
    () => selectedResult?.bounding_boxes || [],
    [selectedResult],
  );

  useEffect(() => {
    return () => {
      if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl);
    };
  }, [pdfBlobUrl]);

  useEffect(() => {
    if (!selectedResult || !numPages) return;
    if (isScrolling.current) return;
    const targetPage = selectedResult.page_number;

    setTimeout(() => {
      const pageEl = pageRefs.current[targetPage];
      const viewer = viewerRef.current;
      if (!pageEl || !viewer) return;

      isScrolling.current = true;
      const pw = pageWidth || MAX_PAGE_WIDTH;
      const box = activeBoxes[0];
      const dims = pageDimensions[targetPage];
      const viewerRect = viewer.getBoundingClientRect();
      const pageRect = pageEl.getBoundingClientRect();
      const relativeTop = pageRect.top - viewerRect.top + viewer.scrollTop;

      if (box && dims) {
        const scale = pw / dims.width;
        viewer.scrollTo({
          top: relativeTop + box.y0 * scale - 80,
          behavior: "smooth",
        });
      } else {
        viewer.scrollTo({ top: relativeTop - 24, behavior: "smooth" });
      }

      setTimeout(() => {
        isScrolling.current = false;
      }, 800);
    }, 300);
  }, [selectedResult, numPages, pageWidth, activeBoxes, pageDimensions]);

  async function fetchMyPdfs() {
    setPdfsLoading(true);
    try {
      const res = await fetch(`${API}/pdfs`, { headers: await authHeaders() });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMyPdfs(data.pdfs || []);
    } catch {
      setAppError("Could not load PDF library.");
    } finally {
      setPdfsLoading(false);
    }
  }

  async function handleDeletePdf(pdfId) {
    if (!window.confirm("Delete this PDF and all its indexed content?")) return;
    setDeletingId(pdfId);
    try {
      const res = await fetch(`${API}/pdfs/${pdfId}`, {
        method: "DELETE",
        headers: await authHeaders(),
      });
      if (!res.ok) throw new Error();
      setMyPdfs((prev) => prev.filter((p) => p.id !== pdfId));
      if (selectedResult?.pdf_id === pdfId) {
        setSelectedResult(null);
        setPdfBlobUrl(null);
        setNumPages(null);
        setLoadedPdfId(null);
      }
      setResults((prev) => prev.filter((r) => r.pdf_id !== pdfId));
    } catch {
      setAppError("Could not delete PDF.");
    } finally {
      setDeletingId(null);
    }
  }

  function openLibrary() {
    setLibraryOpen(true);
    fetchMyPdfs();
  }

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setResults([]);
    setSearched(true);
    setAppError(null);
    try {
      const res = await fetch(`${API}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(await authHeaders()),
        },
        body: JSON.stringify({ query, top_k: 8 }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setResults(data.results || []);
    } catch {
      setAppError("Search failed — make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResultClick(result) {
    const isSamePdf = selectedResult?.pdf_id === result.pdf_id;
    setSelectedResult(result);
    isScrolling.current = false;
    setAppError(null);
    if (isMobile) setMobileView("viewer");

    if (!isSamePdf) {
      setPdfBlobUrl(null);
      setNumPages(null);
      pageRefs.current = {};
      setPageDimensions({});
      setLoadedPdfId(null);
      try {
        const res = await fetch(`${API}/pdf/${result.pdf_id}`, {
          headers: await authHeaders(),
        });
        if (!res.ok) throw new Error();
        const blob = await res.blob();
        setPdfBlobUrl(URL.createObjectURL(blob));
        setLoadedPdfId(result.pdf_id);
      } catch {
        setAppError("Could not load PDF — check your connection.");
      }
    } else {
      setTimeout(() => {
        const pageEl = pageRefs.current[result.page_number];
        const viewer = viewerRef.current;
        if (!pageEl || !viewer) return;
        const viewerRect = viewer.getBoundingClientRect();
        const pageRect = pageEl.getBoundingClientRect();
        const relativeTop = pageRect.top - viewerRect.top + viewer.scrollTop;
        viewer.scrollTo({ top: relativeTop - 24, behavior: "smooth" });
      }, 100);
    }
  }

  async function handleUpload(e) {
    const files = Array.from(e.target.files).filter((f) =>
      f.name.endsWith(".pdf"),
    );
    if (files.length === 0) return;
    setAppError(null);
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setUploadStatus({
          current: i + 1,
          total: files.length,
          filename: file.name,
        });
        const formData = new FormData();
        formData.append("file", file);
        let headers;
        try {
          headers = await authHeaders();
        } catch {
          setAppError("Not logged in — please sign in again.");
          return;
        }
        const res = await fetch(`${API}/ingest`, {
          method: "POST",
          headers,
          body: formData,
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? "Upload failed");
        }
      }
      fetchMyPdfs();
    } catch (err) {
      if (err.message === "NOT_LOGGED_IN") {
        setAppError("Session expired — please sign out and sign in again.");
      } else {
        setAppError(`Upload failed: ${err.message}`);
      }
    } finally {
      setUploadStatus(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (folderInputRef.current) folderInputRef.current.value = "";
    }
  }

  function handlePageLoadSuccess(pageNum, page) {
    setPageDimensions((prev) => ({
      ...prev,
      [pageNum]: { width: page.originalWidth, height: page.originalHeight },
    }));
  }

  const uploadPct = uploadStatus
    ? Math.round((uploadStatus.current / uploadStatus.total) * 100)
    : 0;

  return (
    <>
      <style>{GLOBAL_CSS}</style>
      <div
        style={{
          height: "100dvh",
          overflow: "hidden",
          background: T.cream,
          display: "flex",
          flexDirection: "column",
          color: T.ink,
          fontFamily: "'Inter', system-ui, sans-serif",
        }}
      >
        {/* ══ HEADER ══ */}
        <header
          style={{
            height: 56,
            flexShrink: 0,
            borderBottom: `1px solid ${T.border}`,
            background: T.white,
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            gap: 10,
            position: "relative",
            zIndex: 10,
          }}
        >
          <span
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontStyle: "italic",
              fontWeight: 400,
              fontSize: 17,
              color: T.ink,
              letterSpacing: "-0.01em",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}
          >
            {isMobile ? "Recall" : "Study PDF Search"}
          </span>

          {uploadStatus ? (
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                gap: 8,
                minWidth: 0,
              }}
            >
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadPct}%` }}
                />
              </div>
              <span
                style={{
                  fontSize: 11,
                  color: T.inkFaint,
                  whiteSpace: "nowrap",
                  flexShrink: 0,
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                {uploadStatus.current}/{uploadStatus.total}
              </span>
            </div>
          ) : (
            <div style={{ flex: 1 }} />
          )}

          <div
            className="header-actions"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              flexShrink: 0,
            }}
          >
            {user && (
              <span
                className="header-email desktop-only"
                style={{
                  fontSize: 12,
                  color: T.inkFaint,
                  maxWidth: 160,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {user?.email ?? ""}
              </span>
            )}

            <button
              onClick={openLibrary}
              className="btn-ghost"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                padding: "5px 10px",
              }}
            >
              <Library size={12} />
              <span className="desktop-only">My PDFs</span>
            </button>

            <button
              onClick={() => fileInputRef.current.click()}
              disabled={!!uploadStatus}
              className="btn-ghost"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                padding: "5px 10px",
              }}
            >
              <FileText size={12} />
              <span>PDF</span>
            </button>

            <button
              onClick={() => folderInputRef.current.click()}
              disabled={!!uploadStatus}
              className="btn-primary"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                padding: "6px 10px",
              }}
            >
              <FolderOpen size={12} />
              <span className="desktop-only">Folder</span>
            </button>

            {user && (
              <button
                onClick={onSignOut}
                className="btn-ghost"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  padding: "5px 10px",
                }}
              >
                <LogOut size={12} />
                <span className="desktop-only">Sign out</span>
              </button>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              multiple
              style={{ display: "none" }}
              onChange={handleUpload}
            />
            <input
              ref={folderInputRef}
              type="file"
              accept=".pdf"
              multiple
              webkitdirectory=""
              style={{ display: "none" }}
              onChange={handleUpload}
            />
          </div>
        </header>

        {/* ══ MAIN ══ */}
        <main
          style={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            overflow: "hidden",
            position: "relative",
          }}
        >
          {/* ── LEFT SIDEBAR ── */}
          <aside
            style={{
              width: isMobile ? "100%" : 320,
              flexShrink: 0,
              borderRight: isMobile ? "none" : `1px solid ${T.border}`,
              background: T.sidebarBg,
              display: isMobile && mobileView === "viewer" ? "none" : "flex",
              flexDirection: "column",
            }}
          >
            {appError && (
              <div
                style={{
                  margin: "10px 12px 0",
                  padding: "9px 12px",
                  borderRadius: 7,
                  background: T.dangerBg,
                  border: `1px solid ${T.dangerBorder}`,
                  fontSize: 11,
                  color: T.danger,
                  lineHeight: 1.5,
                }}
              >
                {appError}
              </div>
            )}

            <div style={{ padding: "14px 12px 0", flexShrink: 0 }}>
              <div
                className="search-container"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "8px 8px 8px 11px",
                  borderRadius: 8,
                  border: `1.5px solid ${T.borderMid}`,
                  background: T.white,
                  transition: "border-color 0.2s, box-shadow 0.2s",
                }}
              >
                <Search
                  size={14}
                  color={T.inkFaint}
                  style={{ flexShrink: 0 }}
                />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="Search your PDFs…"
                  style={{
                    flex: 1,
                    background: "none",
                    border: "none",
                    outline: "none",
                    fontSize: 13,
                    color: T.ink,
                    fontFamily: "'Inter', sans-serif",
                  }}
                />
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  className="btn-primary"
                  style={{ padding: "5px 11px", fontSize: 12, flexShrink: 0 }}
                >
                  {loading ? "…" : "Search"}
                </button>
              </div>

              {!loading && results.length > 0 && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                    padding: "9px 2px 0",
                  }}
                >
                  <Sparkles size={10} color={T.amber} />
                  <span style={{ fontSize: 11, color: T.inkFaint }}>
                    {results.length} results for "{query}"
                  </span>
                </div>
              )}
            </div>

            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "10px 12px 14px",
                display: "flex",
                flexDirection: "column",
                gap: 6,
              }}
            >
              {loading && (
                <>
                  {[1, 2, 3].map((i) => (
                    <SkeletonCard key={i} />
                  ))}
                  <p
                    style={{
                      textAlign: "center",
                      fontSize: 11,
                      color: T.inkFaint,
                      marginTop: 4,
                    }}
                  >
                    Searching…
                  </p>
                </>
              )}
              {!loading && searched && results.length === 0 && (
                <EmptyState
                  icon={Search}
                  title="No results found"
                  subtitle="Try a different query — or upload more documents."
                />
              )}
              {!loading && !searched && (
                <EmptyState
                  icon={FileText}
                  title="Search your documents"
                  subtitle="Type a question or topic to find relevant passages across all your PDFs."
                />
              )}
              {!loading &&
                results.map((r, i) => (
                  <div
                    key={i}
                    className={`result-card fade-up ${selectedResult === r ? "active" : ""}`}
                    style={{ animationDelay: `${i * 50}ms` }}
                    onClick={() => handleResultClick(r)}
                  >
                    <div
                      style={{
                        fontSize: 10,
                        color: T.inkFaint,
                        fontWeight: 500,
                        marginBottom: 6,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                      }}
                    >
                      <FileText size={10} />
                      {r.original_filename}
                    </div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: 7,
                      }}
                    >
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 600,
                          color: T.amber,
                          display: "flex",
                          alignItems: "center",
                          gap: 3,
                        }}
                      >
                        <ChevronRight size={11} />
                        Page {r.page_number}
                      </span>
                      <ScorePill score={r.score} />
                    </div>
                    <p
                      style={{
                        margin: 0,
                        fontSize: 12,
                        color: T.inkMid,
                        lineHeight: 1.6,
                        display: "-webkit-box",
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {r.chunk_text}
                    </p>
                  </div>
                ))}
            </div>
          </aside>

          {/* ── RIGHT PANEL (PDF viewer) ── */}
          {(!isMobile || mobileView === "viewer") && (
            <div
              className={isMobile ? "slide-up" : ""}
              style={
                isMobile
                  ? {
                      position: "fixed",
                      inset: 0,
                      zIndex: 50,
                      background: T.cream,
                      display: "flex",
                      flexDirection: "column",
                    }
                  : {
                      flex: 1,
                      minWidth: 0,
                      display: "flex",
                      flexDirection: "column",
                      overflow: "hidden",
                    }
              }
            >
              <PDFViewerContent
                isMobile={isMobile}
                setMobileView={setMobileView}
                selectedResult={selectedResult}
                pdfBlobUrl={pdfBlobUrl}
                pageWidth={pageWidth}
                numPages={numPages}
                pageDimensions={pageDimensions}
                loadedPdfId={loadedPdfId}
                activeBoxes={activeBoxes}
                viewerRef={viewerRef}
                viewerWidthRef={viewerWidthRef}
                pageRefs={pageRefs}
                handlePageLoadSuccess={handlePageLoadSuccess}
              />
            </div>
          )}

          {/* ── MY PDFs SLIDE-IN PANEL ── */}
          {libraryOpen && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                zIndex: 30,
                display: "flex",
              }}
            >
              <div
                onClick={() => setLibraryOpen(false)}
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "rgba(26,23,20,0.35)",
                  backdropFilter: "blur(2px)",
                }}
              />
              <div
                style={{
                  position: "relative",
                  width: isMobile ? "100%" : 380,
                  background: T.white,
                  borderRight: isMobile ? "none" : `1px solid ${T.border}`,
                  display: "flex",
                  flexDirection: "column",
                  boxShadow: "4px 0 32px rgba(26,23,20,0.12)",
                  animation: "slideIn 0.25s ease",
                }}
              >
                <div
                  style={{
                    padding: "16px 18px",
                    borderBottom: `1px solid ${T.border}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexShrink: 0,
                  }}
                >
                  <div>
                    <p
                      style={{
                        fontSize: 14,
                        fontWeight: 700,
                        color: T.ink,
                        fontFamily: "'Playfair Display', serif",
                        fontStyle: "italic",
                      }}
                    >
                      My Library
                    </p>
                    <p
                      style={{ fontSize: 11, color: T.inkFaint, marginTop: 2 }}
                    >
                      {myPdfs.length} document{myPdfs.length !== 1 ? "s" : ""}{" "}
                      indexed
                    </p>
                  </div>
                  <button
                    onClick={() => setLibraryOpen(false)}
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: T.inkFaint,
                      display: "flex",
                      alignItems: "center",
                      padding: 4,
                      borderRadius: 6,
                    }}
                  >
                    <X size={16} />
                  </button>
                </div>

                <div
                  style={{
                    flex: 1,
                    overflowY: "auto",
                    padding: "12px 14px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  {pdfsLoading &&
                    [1, 2, 3].map((i) => <SkeletonCard key={i} />)}
                  {!pdfsLoading && myPdfs.length === 0 && (
                    <EmptyState
                      icon={Library}
                      title="No documents yet"
                      subtitle="Upload a PDF or folder to get started."
                    />
                  )}
                  {!pdfsLoading &&
                    myPdfs.map((pdf) => (
                      <div key={pdf.id} className="pdf-item">
                        <div
                          style={{
                            width: 36,
                            height: 36,
                            borderRadius: 8,
                            background: T.amberBg,
                            border: `1px solid rgba(196,131,10,0.2)`,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            flexShrink: 0,
                          }}
                        >
                          <FileText size={16} color={T.amber} />
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p
                            style={{
                              fontSize: 12,
                              fontWeight: 600,
                              color: T.ink,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {pdf.filename}
                          </p>
                          <p
                            style={{
                              fontSize: 10,
                              color: T.inkFaint,
                              marginTop: 2,
                              fontFamily: "'JetBrains Mono', monospace",
                            }}
                          >
                            {pdf.total_pages} pages ·{" "}
                            {pdf.upload_date?.slice(0, 10) ?? ""}
                          </p>
                        </div>
                        <button
                          className="delete-btn"
                          onClick={() => handleDeletePdf(pdf.id)}
                          disabled={deletingId === pdf.id}
                          title="Delete PDF"
                        >
                          {deletingId === pdf.id ? (
                            <div
                              style={{
                                width: 14,
                                height: 14,
                                border: `2px solid ${T.borderMid}`,
                                borderTopColor: T.danger,
                                borderRadius: "50%",
                                animation: "spin 0.8s linear infinite",
                              }}
                            />
                          ) : (
                            <Trash2 size={14} />
                          )}
                        </button>
                      </div>
                    ))}
                </div>

                <div
                  style={{
                    padding: "12px 14px",
                    borderTop: `1px solid ${T.border}`,
                    display: "flex",
                    gap: 8,
                    flexShrink: 0,
                  }}
                >
                  <button
                    onClick={() => {
                      setLibraryOpen(false);
                      fileInputRef.current.click();
                    }}
                    disabled={!!uploadStatus}
                    className="btn-ghost"
                    style={{
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 5,
                      padding: "7px 0",
                    }}
                  >
                    <FileText size={12} /> Add PDF
                  </button>
                  <button
                    onClick={() => {
                      setLibraryOpen(false);
                      folderInputRef.current.click();
                    }}
                    disabled={!!uploadStatus}
                    className="btn-primary"
                    style={{
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 5,
                      padding: "7px 0",
                    }}
                  >
                    <FolderOpen size={12} /> Add Folder
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
