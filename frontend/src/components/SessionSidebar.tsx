import { useCallback, useEffect, useState } from "react";
import { deleteSession, fetchSessions } from "../api/client";
import type { SessionSummary } from "../api/types";

interface Props {
  activeSessionId?: string;
  refreshToken: number;
  onSelect: (sessionId: string) => void;
  onNew: () => void;
  className?: string;
}

function formatSessionTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const sameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();
  if (sameDay) {
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  }
  return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}

/** 左侧会话列表：历史记录与删除 */
export default function SessionSidebar({
  activeSessionId,
  refreshToken,
  onSelect,
  onNew,
  className = "",
}: Props) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch {
      setSessions([]);
      setError("无法加载历史对话");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshToken]);

  async function handleDelete(sessionId: string) {
    if (deletingId) return;
    setDeletingId(sessionId);
    setError(null);
    try {
      await deleteSession(sessionId);
      if (activeSessionId === sessionId) onNew();
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch {
      setError("删除失败，请确认后端已启动后重试");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <aside
      className={`flex flex-col border-r border-[var(--nc-border)] bg-white/80 ${className}`}
    >
      <div className="p-3 border-b border-[var(--nc-border)]">
        <button
          type="button"
          onClick={onNew}
          className="w-full py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-[var(--nc-navy)] to-[var(--nc-navy-deep)] hover:opacity-95 transition-opacity"
        >
          + 新对话
        </button>
      </div>

      {error && (
        <p className="mx-2 mt-2 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-2 py-1.5">
          {error}
        </p>
      )}

      <div className="flex-1 overflow-y-auto p-2 space-y-0.5 min-h-0">
        {loading && (
          <p className="text-xs text-[var(--nc-muted)] text-center py-6">加载历史…</p>
        )}
        {!loading && sessions.length === 0 && (
          <p className="text-xs text-[var(--nc-muted)] text-center py-6 px-2 leading-relaxed">
            暂无历史对话
          </p>
        )}
        {sessions.map((session) => {
          const active = session.id === activeSessionId;
          const isDeleting = deletingId === session.id;
          return (
            <div
              key={session.id}
              className={`group flex items-stretch gap-0.5 rounded-xl transition-opacity ${
                isDeleting ? "opacity-50 pointer-events-none" : ""
              } ${
                active
                  ? "bg-[var(--nc-navy)]/8 border border-[var(--nc-navy)]/15"
                  : "hover:bg-[var(--nc-bg)] border border-transparent"
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(session.id)}
                className="flex-1 min-w-0 text-left px-3 py-2.5"
                disabled={isDeleting}
              >
                <p
                  className={`text-sm font-medium truncate ${
                    active ? "text-[var(--nc-navy)]" : "text-slate-700"
                  }`}
                >
                  {session.title || "新对话"}
                </p>
                <p className="text-[10px] text-[var(--nc-muted)] mt-0.5">
                  {formatSessionTime(session.created_at)}
                </p>
              </button>
              <button
                type="button"
                title="删除此对话"
                onClick={() => handleDelete(session.id)}
                disabled={deletingId !== null}
                className="shrink-0 w-9 flex items-center justify-center text-[var(--nc-muted)] hover:text-red-600 hover:bg-red-50 rounded-lg mr-1 self-center opacity-70 md:opacity-0 md:group-hover:opacity-100 focus:opacity-100 transition-all"
                aria-label="删除对话"
              >
                {isDeleting ? (
                  <span className="w-3 h-3 border-2 border-[var(--nc-muted)] border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
