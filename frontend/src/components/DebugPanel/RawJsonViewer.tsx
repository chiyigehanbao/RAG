import { useState } from "react";
import type { TracePayload } from "../../api/types";

interface Props {
  data: TracePayload;
}

export default function RawJsonViewer({ data }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <section className="pt-2 border-t border-[var(--nc-border)]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs text-[var(--nc-muted)] hover:text-[var(--nc-navy)] transition-colors"
      >
        <span className="px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wide bg-slate-100 font-medium">
          开发者
        </span>
        {open ? "收起原始 JSON" : "展开原始 JSON"}
      </button>
      {open && (
        <pre className="mt-2 text-[10px] font-mono-nc bg-[var(--nc-navy-deep)] text-slate-200 p-3 rounded-xl overflow-auto max-h-56 leading-relaxed">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </section>
  );
}
