interface Props {
  className?: string;
  size?: "sm" | "md";
}

/** NovaCloud 品牌标志（抽象云形） */
export default function Logo({ className = "", size = "md" }: Props) {
  const dim = size === "sm" ? 28 : 36;

  return (
    <svg
      width={dim}
      height={dim}
      viewBox="0 0 36 36"
      fill="none"
      className={className}
      aria-hidden
    >
      <rect width="36" height="36" rx="10" fill="url(#nc-logo-grad)" />
      <path
        d="M11 22c0-2.8 2.2-5 5-5 .6 0 1.2.1 1.7.3C18.2 14.8 20.4 13 23 13c3.3 0 6 2.7 6 6 0 .3 0 .6-.05.9.8.4 1.35 1.2 1.35 2.1 0 1.4-1.1 2.5-2.5 2.5H13.5c-1.4 0-2.5-1.1-2.5-2.5 0-1.2.8-2.2 2-2.4Z"
        fill="white"
        fillOpacity="0.95"
      />
      <defs>
        <linearGradient id="nc-logo-grad" x1="0" y1="0" x2="36" y2="36">
          <stop stopColor="#0b3d5c" />
          <stop offset="1" stopColor="#14b8a6" />
        </linearGradient>
      </defs>
    </svg>
  );
}
