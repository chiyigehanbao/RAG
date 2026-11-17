import { Fragment, useState } from "react";
import { fetchDocumentChunks } from "../api/client";
import type { DocumentChunk, DocumentItem } from "../api/types";
import { friendlySource } from "../lib/labels";
import EmptyState from "./EmptyState";

interface Props {
  documents: DocumentItem[];
  loading: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  indexed: "已入库",
  ready: "已入库",
  pending: "待入库",
};

function statusLabel(status: string): string {
  const key = status.toLowerCase();
  if (STATUS_LABELS[key]) return STATUS_LABELS[key];
  if (key.includes("index")) return "已入库";
  return status;
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const isReady = normalized.includes("index") || normalized === "ready" || normalized === "indexed";
  const label = statusLabel(status);

  return (
    <span
      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
        isReady
          ? "bg-emerald-50 text-emerald-700 border border-emerald-100"
          : "bg-amber-50 text-amber-700 border border-amber-100"
      }`}
    >
      {label}
    </span>
  );
}

export default function DocumentTable({ documents, loading }: Props) {
  const [expandedPath, setExpandedPath] = useState<string | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [chunksError, setChunksError] = useState<string | null>(null);

  async function toggleChunks(path: string) {
    if (expandedPath === path) {
      setExpandedPath(null);
      setChunks([]);
      return;
    }
    setExpandedPath(path);
    setChunksLoading(true);
    setChunksError(null);
    try {
      const data = await fetchDocumentChunks(path);
      setChunks(data);
    } catch {
      setChunksError("无法加载分块预览");
      setChunks([]);
    } finally {
      setChunksLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-sm text-[var(--nc-muted)]">
        <span className="flex gap-1 mr-2">
          <span className="nc-loading-dot w-1.5 h-1.5 rounded-full bg-[var(--nc-teal)]" />
          <span className="nc-loading-dot w-1.5 h-1.5 rounded-full bg-[var(--nc-teal)]" />
          <span className="nc-loading-dot w-1.5 h-1.5 rounded-full bg-[var(--nc-teal)]" />
        </span>
        加载文档列表…
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <EmptyState
        title="暂无已入库文档"
        description="请在项目根目录运行 ingest，或点击「重新索引」"
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-[var(--nc-border)] bg-white shadow-[var(--nc-shadow-lg)] nc-animate-in">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gradient-to-r from-[var(--nc-navy)]/5 to-transparent text-[var(--nc-muted)] text-xs uppercase tracking-wider">
            <th className="text-left px-5 py-3 font-display font-semibold">文档</th>
            <th className="text-left px-5 py-3 font-display font-semibold">状态</th>
            <th className="text-right px-5 py-3 font-display font-semibold">片段数</th>
            <th className="w-24 px-3 font-display font-semibold text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc, index) => (
            <Fragment key={doc.id}>
              <tr
                className={`border-t border-[var(--nc-border)]/80 ${
                  index % 2 === 1 ? "bg-[var(--nc-bg)]/50" : ""
                }`}
              >
                <td className="px-5 py-3.5">
                  <p className="font-medium text-[var(--nc-navy)]">{friendlySource(doc.path)}</p>
                  <p className="font-mono-nc text-[10px] text-[var(--nc-muted)] mt-0.5">{doc.path}</p>
                </td>
                <td className="px-5 py-3.5">
                  <StatusPill status={doc.status} />
                </td>
                <td className="px-5 py-3.5 text-right font-medium text-[var(--nc-navy)] tabular-nums">
                  {doc.chunk_count}
                </td>
                <td className="px-3 py-3.5 text-right">
                  <button
                    type="button"
                    onClick={() => toggleChunks(doc.path)}
                    className="text-xs text-[var(--nc-teal)] hover:underline"
                  >
                    {expandedPath === doc.path ? "收起" : "看片段"}
                  </button>
                </td>
              </tr>
              {expandedPath === doc.path && (
                <tr key={`${doc.id}-chunks`} className="bg-[var(--nc-bg)]/80">
                  <td colSpan={4} className="px-5 py-4">
                    {chunksLoading && (
                      <p className="text-xs text-[var(--nc-muted)]">加载片段列表…</p>
                    )}
                    {chunksError && (
                      <p className="text-xs text-red-600">{chunksError}</p>
                    )}
                    {!chunksLoading && !chunksError && chunks.length > 0 && (
                      <ol className="space-y-2 max-h-64 overflow-y-auto">
                        {chunks.map((chunk) => (
                          <li
                            key={chunk.index}
                            className="text-xs border border-[var(--nc-border)] rounded-lg p-3 bg-white"
                          >
                            <div className="flex justify-between gap-2 text-[var(--nc-muted)] mb-1">
                              <span>
                                第 {chunk.index + 1} 段 · {chunk.section || "（无章节标题）"}
                              </span>
                              <span>共 {chunk.char_count} 字</span>
                            </div>
                            <p className="text-[var(--nc-navy)] leading-relaxed">{chunk.preview}…</p>
                          </li>
                        ))}
                      </ol>
                    )}
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
