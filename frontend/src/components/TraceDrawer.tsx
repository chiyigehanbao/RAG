import { useEffect } from "react";
import type { TraceNode, TracePayload } from "../api/types";
import { formatCitation, gradeReasonLabel, NODE_LABELS, ROUTE_LABELS } from "../lib/labels";
import RawJsonViewer from "./DebugPanel/RawJsonViewer";

interface Props {
  trace: TracePayload;
  open: boolean;
  onClose: () => void;
}

function RewriteCompareCard({
  originalQuery,
  rewrittenQuery,
  retryCount,
}: {
  originalQuery: string;
  rewrittenQuery: string;
  retryCount?: number;
}) {
  return (
    <section className="rounded-xl border border-[var(--nc-teal)]/25 bg-[var(--nc-teal)]/8 p-4">
      <p className="text-xs font-semibold text-[var(--nc-navy)] mb-3">查询改写对比</p>
      {retryCount != null && (
        <p className="text-[11px] text-[var(--nc-muted)] mb-2">第 {retryCount} 次改写</p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div className="rounded-lg bg-white/80 border border-[var(--nc-border)] p-3">
          <p className="text-[10px] uppercase tracking-wide text-[var(--nc-muted)] mb-1">原 query</p>
          <p className="text-[var(--nc-navy)] leading-relaxed break-words">{originalQuery}</p>
        </div>
        <div className="rounded-lg bg-white/80 border border-[var(--nc-teal)]/30 p-3">
          <p className="text-[10px] uppercase tracking-wide text-[var(--nc-muted)] mb-1">改写后</p>
          <p className="text-[var(--nc-navy)] leading-relaxed break-words">{rewrittenQuery}</p>
        </div>
      </div>
    </section>
  );
}

function nodeDetail(node: TraceNode): string | null {
  if (node.name === "classify") {
    const route = (node.output as { route?: string }).route;
    return route ? `决策：${ROUTE_LABELS[route] ?? route}` : null;
  }
  if (node.name === "grade") {
    const out = node.output as { grade_reason?: string; min_distance?: number };
    const parts = [gradeReasonLabel(out.grade_reason)];
    if (out.min_distance != null) parts.push(`匹配度 ${out.min_distance}`);
    return parts.filter(Boolean).join(" · ");
  }
  if (node.name === "rewrite") {
    return null;
  }
  if (node.name === "retrieve") {
    const q = (node.input as { query?: string }).query;
    return q ? `检索：${q}` : null;
  }
  return null;
}

/** 可选查看：单次回答的过程（含改写） */
export default function TraceDrawer({ trace, open, onClose }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const totalMs = trace.nodes.reduce((s, n) => s + n.duration_ms, 0);
  const rewriteNodes = trace.nodes.filter((n) => n.name === "rewrite");

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        className="absolute inset-0 bg-[var(--nc-navy-deep)]/40 backdrop-blur-sm"
        aria-label="关闭"
        onClick={onClose}
      />
      <div className="relative w-full max-w-md h-full bg-white shadow-2xl flex flex-col animate-[nc-fade-up_0.25s_ease-out]">
        <header className="px-5 py-4 border-b border-[var(--nc-border)] flex justify-between items-center">
          <div>
            <h3 className="font-display font-semibold text-[var(--nc-navy)]">本次回答过程</h3>
            <p className="text-xs text-[var(--nc-muted)] mt-0.5">共耗时约 {totalMs} 毫秒</p>
          </div>
          <button type="button" onClick={onClose} className="text-[var(--nc-muted)] hover:text-[var(--nc-navy)] p-2">
            ✕
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {rewriteNodes.map((node, i) => {
            const out = node.output as { rewritten_query?: string; retry_count?: number };
            const inp = node.input as { last_query?: string; original_query?: string };
            if (!out.rewritten_query) return null;
            const original =
              inp.last_query ?? inp.original_query ?? trace.question;
            return (
              <RewriteCompareCard
                key={i}
                originalQuery={original}
                rewrittenQuery={out.rewritten_query}
                retryCount={out.retry_count}
              />
            );
          })}
          <ol className="space-y-3">
            {trace.nodes.map((node, i) => {
              const detail = nodeDetail(node);
              return (
                <li key={`${node.name}-${i}`} className="flex gap-3 text-sm">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-[var(--nc-teal)]/20 text-[var(--nc-navy)] text-xs flex items-center justify-center font-medium">
                    {i + 1}
                  </span>
                  <div className="min-w-0">
                    <p className="font-medium text-[var(--nc-navy)]">{NODE_LABELS[node.name] ?? node.name}</p>
                    <p className="text-xs text-[var(--nc-muted)]">{node.duration_ms} 毫秒</p>
                    {detail && <p className="text-xs mt-1 text-[var(--nc-muted)] leading-relaxed">{detail}</p>}
                  </div>
                </li>
              );
            })}
          </ol>
          {trace.citations.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-[var(--nc-muted)] uppercase mb-2">参考来源</h4>
              <ul className="text-xs space-y-1.5">
                {trace.citations.map((c, i) => (
                  <li key={i} className="text-[var(--nc-navy)]">
                    {formatCitation(c.source, c.section)}
                  </li>
                ))}
              </ul>
            </section>
          )}
          <RawJsonViewer data={trace} />
        </div>
      </div>
    </div>
  );
}
