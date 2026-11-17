import { useEffect, useRef } from "react";
import type { TracePayload } from "../../api/types";
import EmptyState from "../EmptyState";
import RawJsonViewer from "./RawJsonViewer";
import RetrieveDetails from "./RetrieveDetails";
import TraceTimeline from "./TraceTimeline";

interface Props {
  trace: TracePayload | null;
}

export default function DebugPanel({ trace }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (trace && containerRef.current) {
      containerRef.current.classList.remove("nc-trace-flash");
      void containerRef.current.offsetWidth;
      containerRef.current.classList.add("nc-trace-flash");
    }
  }, [trace?.message_id]);

  if (!trace) {
    return <EmptyState icon="insight" title="等待首个问题" description="提问后将展示 Agent 分类、检索与生成过程" />;
  }

  return (
    <div ref={containerRef} className="p-4 space-y-6">
      <TraceTimeline nodes={trace.nodes} />
      <RetrieveDetails nodes={trace.nodes} />
      <section>
        <h3 className="text-xs font-display font-semibold uppercase tracking-wider text-[var(--nc-muted)] mb-2">
          引用溯源
        </h3>
        {trace.citations.length === 0 ? (
          <p className="text-xs text-[var(--nc-muted)]">本次回答无文档引用</p>
        ) : (
          <ul className="space-y-1.5">
            {trace.citations.map((citation, index) => (
              <li
                key={index}
                className="text-xs flex items-start gap-2 p-2 rounded-lg bg-white border border-[var(--nc-border)]"
              >
                <svg className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[var(--nc-teal-dim)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                <span className="font-mono-nc text-[var(--nc-navy)] leading-relaxed">
                  {citation.source}
                  <span className="text-[var(--nc-muted)]"> · {citation.section}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <RawJsonViewer data={trace} />
    </div>
  );
}
