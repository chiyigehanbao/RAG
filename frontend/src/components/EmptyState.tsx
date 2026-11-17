interface Props {
  title: string;
  description?: string;
  icon?: "docs" | "insight";
}

export default function EmptyState({ title, description, icon = "docs" }: Props) {
  return (
    <div className="flex flex-col items-center justify-center text-center px-6 py-12">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--nc-navy)]/10 to-[var(--nc-teal)]/20 flex items-center justify-center mb-4">
        {icon === "insight" ? (
          <svg className="w-7 h-7 text-[var(--nc-navy)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        ) : (
          <svg className="w-7 h-7 text-[var(--nc-navy)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        )}
      </div>
      <p className="font-display font-semibold text-[var(--nc-navy)] text-base">{title}</p>
      {description && (
        <p className="text-sm text-[var(--nc-muted)] mt-2 max-w-xs leading-relaxed">{description}</p>
      )}
    </div>
  );
}
