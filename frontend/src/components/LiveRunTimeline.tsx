import type { RunStep } from "../api/types";
import { NODE_LABELS, ROUTE_LABELS, gradeReasonLabel } from "../lib/labels";

export type { RunStep };

interface Props {
  steps: RunStep[];
  active?: boolean;
}

function detailText(step: RunStep): string | null {
  const d = step.detail || {};
  if (step.name === "classify" && d.route) {
    return `决策：${ROUTE_LABELS[String(d.route)] ?? String(d.route)}`;
  }
  if (step.name === "grade") {
    const parts = [gradeReasonLabel(String(d.grade_reason ?? ""))];
    if (d.min_distance != null) parts.push(`匹配度 ${d.min_distance}`);
    return parts.filter(Boolean).join(" · ");
  }
  if (step.name === "rewrite" && d.rewritten_query) {
    const last = d.last_query != null ? String(d.last_query) : "原问";
    const retry = d.retry_count != null ? `（第 ${d.retry_count} 次）` : "";
    return `「${last}」→「${String(d.rewritten_query)}」${retry}`;
  }
  if (step.name === "retrieve") {
    const parts: string[] = [];
    if (d.top_k != null) parts.push(`${d.top_k} 个片段`);
    if (d.min_distance != null) parts.push(`最近距离 ${d.min_distance}`);
    return parts.length ? parts.join(" · ") : null;
  }
  return null;
}

/** LangGraph 执行链路（流式追加） */
export default function LiveRunTimeline({ steps, active }: Props) {
  if (steps.length === 0 && !active) return null;

  return (
    <div className="mb-4 rounded-xl border border-[var(--nc-navy)]/15 bg-[var(--nc-navy)]/5 p-4">
      <p className="text-xs font-display font-semibold text-[var(--nc-navy)] mb-3 flex items-center gap-2">
        {active && (
          <span className="w-2 h-2 rounded-full bg-[var(--nc-teal)] animate-pulse" />
        )}
        LangGraph 执行链路
      </p>
      <ol className="space-y-2">
        {steps.map((step, i) => (
          <li key={step.id} className="flex gap-3 text-sm">
            <span
              className={`shrink-0 w-6 h-6 rounded-full text-xs flex items-center justify-center font-medium ${
                step.status === "running"
                  ? "bg-[var(--nc-teal)]/30 text-[var(--nc-navy)]"
                  : "bg-[var(--nc-navy)]/10 text-[var(--nc-navy)]"
              }`}
            >
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex justify-between gap-2">
                <span className="font-medium text-[var(--nc-navy)]">
                  {NODE_LABELS[step.name] ?? step.name}
                  {step.status === "running" && (
                    <span className="text-[var(--nc-muted)] font-normal ml-1">…</span>
                  )}
                </span>
                {step.duration_ms > 0 && (
                  <span className="text-xs text-[var(--nc-muted)] shrink-0">{step.duration_ms} ms</span>
                )}
              </div>
              {detailText(step) && (
                <p className="text-xs text-[var(--nc-muted)] mt-0.5 leading-relaxed">{detailText(step)}</p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
