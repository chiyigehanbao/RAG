import type { Citation } from "../api/types";
import { formatCitation } from "../lib/labels";

interface Props {
  citations: Citation[];
}

export default function CitationBadge({ citations }: Props) {
  if (citations.length === 0) return null;

  const unique = citations.filter(
    (c, i, arr) => arr.findIndex((x) => x.source === c.source && x.section === c.section) === i,
  );

  return (
    <div className="mt-3 pt-3 border-t border-[var(--nc-border)]">
      <p className="text-[10px] uppercase tracking-wider text-[var(--nc-muted)] mb-2 font-medium">参考文档</p>
      <div className="flex flex-wrap gap-1.5">
        {unique.map((citation, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full bg-[var(--nc-navy)]/5 text-[var(--nc-navy)] border border-[var(--nc-navy)]/10"
            title={`${citation.source} · ${citation.section}`}
          >
            <svg className="w-3 h-3 shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {formatCitation(citation.source, citation.section)}
          </span>
        ))}
      </div>
    </div>
  );
}
