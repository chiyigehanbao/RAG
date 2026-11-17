import CitationBadge from "./CitationBadge";
import LiveRunTimeline from "./LiveRunTimeline";
import Logo from "./Logo";
import type { ChatMessage } from "../api/types";
import { formatAssistantText } from "../lib/formatAnswer";

interface Props {
  message: ChatMessage;
  onViewProcess?: () => void;
}

export default function MessageBubble({ message, onViewProcess }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end nc-msg-enter">
        <div className="max-w-[85%] rounded-2xl rounded-br-md px-4 py-3 text-sm leading-relaxed text-white bg-gradient-to-br from-[var(--nc-navy)] to-[var(--nc-navy-deep)] shadow-[var(--nc-shadow)]">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  const body = formatAssistantText(message.content);
  const hasBody = body.trim().length > 0;
  const hasTimeline = Boolean(message.runSteps?.length);

  return (
    <div className="flex gap-3 justify-start nc-msg-enter">
      <div className="shrink-0 mt-1">
        <Logo size="sm" />
      </div>
      <div className="max-w-[85%] min-w-0 space-y-2">
        {hasTimeline && (
          <LiveRunTimeline
            steps={message.runSteps!}
            active={message.runSteps!.some((s) => s.status === "running")}
          />
        )}
        {hasBody && (
          <div className="rounded-2xl rounded-bl-md px-4 py-3 text-sm leading-relaxed bg-white border border-[var(--nc-border)] text-slate-800 shadow-[var(--nc-shadow)]">
            <p className="whitespace-pre-wrap">{body}</p>
            {message.citations && message.citations.length > 0 && (
              <CitationBadge citations={message.citations} />
            )}
          </div>
        )}
        {onViewProcess && hasBody && (
          <button
            type="button"
            onClick={onViewProcess}
            className="mt-2 text-xs text-[var(--nc-muted)] hover:text-[var(--nc-navy)] underline-offset-2 hover:underline"
          >
            查看本次回答过程
          </button>
        )}
      </div>
    </div>
  );
}
