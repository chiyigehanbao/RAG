import type { TraceNode } from "../../api/types";

const NODE_META: Record<string, { label: string; color: string }> = {
  classify: { label: "意图分类", color: "bg-violet-500" },
  retrieve: { label: "向量检索", color: "bg-[var(--nc-teal)]" },
  generate: { label: "生成回答", color: "bg-[var(--nc-navy)]" },
  refuse: { label: "安全拒答", color: "bg-amber-500" },
  chitchat: { label: "闲聊", color: "bg-slate-400" },
};

interface Props {
  nodes: TraceNode[];
}

export default function TraceTimeline({ nodes }: Props) {
  const computedTotal = nodes.reduce((sum, node) => sum + node.duration_ms, 0) || 1;
  const displayTotal = computedTotal;

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-xs font-display font-semibold uppercase tracking-wider text-[var(--nc-muted)]">
          执行步骤
        </h3>
        <span className="text-[11px] text-[var(--nc-muted)] font-mono-nc">{displayTotal} ms</span>
      </div>
      <ol className="relative space-y-0 pl-1">
        {nodes.map((node, index) => {
          const meta = NODE_META[node.name] ?? { label: node.name, color: "bg-slate-400" };
          const isLast = index === nodes.length - 1;
          const widthPct = Math.max((node.duration_ms / computedTotal) * 100, 8);

          return (
            <li key={`${node.name}-${index}`} className="relative flex gap-3 pb-4">
              {!isLast && (
                <span
                  className="absolute left-[11px] top-6 bottom-0 w-px bg-[var(--nc-border)]"
                  aria-hidden
                />
              )}
              <span
                className={`relative z-10 shrink-0 w-[22px] h-[22px] rounded-full ${meta.color} ring-4 ring-white flex items-center justify-center`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-white/90" />
              </span>
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex justify-between items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-[var(--nc-navy)]">{meta.label}</span>
                  <span className="text-[11px] font-mono-nc text-[var(--nc-muted)] shrink-0">
                    {node.duration_ms} ms
                  </span>
                </div>
                <div className="h-1.5 bg-[var(--nc-bg-warm)] rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${meta.color} opacity-80 transition-all duration-500`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
                <p className="text-[10px] text-[var(--nc-muted)] mt-1 font-mono-nc">{node.name}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
