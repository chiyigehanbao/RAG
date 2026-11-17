import type { RetrieveChunk, TraceNode } from "../../api/types";

interface Props {
  nodes: TraceNode[];
}

function getRetrieveChunks(nodes: TraceNode[]): RetrieveChunk[] {
  const retrieveNode = nodes.find((node) => node.name === "retrieve");
  if (!retrieveNode) return [];

  const output = retrieveNode.output as { chunks?: RetrieveChunk[] };
  return output.chunks ?? [];
}

function distanceBarColor(distance: number | undefined): string {
  if (distance == null) return "bg-slate-300";
  if (distance < 200) return "bg-emerald-500";
  if (distance < 350) return "bg-[var(--nc-teal)]";
  return "bg-amber-400";
}

export default function RetrieveDetails({ nodes }: Props) {
  const chunks = getRetrieveChunks(nodes);
  const classifyNode = nodes.find((node) => node.name === "classify");
  const route = classifyNode
    ? String((classifyNode.output as { route?: string }).route ?? "unknown")
    : null;

  const maxDistance = Math.max(...chunks.map((c) => c.distance ?? 0), 450);

  return (
    <section className="space-y-3">
      <h3 className="text-xs font-display font-semibold uppercase tracking-wider text-[var(--nc-muted)]">
        检索详情
      </h3>

      {route && (
        <div className="text-xs flex items-center gap-2 p-2.5 rounded-xl bg-[var(--nc-navy)]/5 border border-[var(--nc-navy)]/10">
          <span className="text-[var(--nc-muted)]">路由决策</span>
          <span className="font-mono-nc font-medium text-[var(--nc-navy)]">{route}</span>
        </div>
      )}

      {chunks.length === 0 ? (
        <p className="text-xs text-[var(--nc-muted)]">暂无检索片段（可能走了闲聊或未检索分支）</p>
      ) : (
        <ul className="space-y-2">
          {chunks.map((chunk, index) => {
            const dist = chunk.distance ?? 0;
            const barPct = Math.min(100, Math.max(8, (1 - dist / maxDistance) * 100));

            return (
              <li
                key={`${chunk.source}-${index}`}
                className="text-xs border border-[var(--nc-border)] rounded-xl p-3 bg-white shadow-sm"
              >
                <div className="flex justify-between gap-2 mb-2">
                  <span className="font-mono-nc text-[var(--nc-navy)] truncate text-[11px]">
                    {chunk.source}
                  </span>
                  <span className="shrink-0 font-mono-nc text-[var(--nc-muted)]">
                    d={chunk.distance ?? "—"}
                  </span>
                </div>
                <div className="h-1 rounded-full bg-[var(--nc-bg)] mb-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${distanceBarColor(chunk.distance)} transition-all`}
                    style={{ width: `${barPct}%` }}
                  />
                </div>
                <p className="text-[var(--nc-muted)] mb-1.5 font-medium">§ {chunk.section}</p>
                <p className="text-slate-600 line-clamp-2 leading-relaxed">{chunk.content.slice(0, 140)}…</p>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
