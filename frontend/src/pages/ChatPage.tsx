import { useCallback, useEffect, useRef, useState } from "react";
import { fetchSessionMessages, fetchTrace, streamChat } from "../api/client";
import type { ChatMessage, TracePayload } from "../api/types";
import LiveRunTimeline, { type RunStep } from "../components/LiveRunTimeline";
import { traceNodesToRunSteps } from "../lib/traceSteps";
import MessageBubble from "../components/MessageBubble";
import SessionSidebar from "../components/SessionSidebar";
import TraceDrawer from "../components/TraceDrawer";
import { useProductName } from "../context/AssistantContext";

const SAMPLE_QUESTIONS = [
  {
    label: "从用户提问到生成答案，Agent 会经过哪些步骤？",
    hint: "对话页展示 LangGraph 执行链路",
    tag: "架构总览",
    icon: "🔀",
  },
  {
    label: "企业版如何计费？",
    hint: "业务 FAQ，带引用来源",
    tag: "业务 FAQ",
    icon: "💳",
  },
  {
    label: "火星怎么登录？",
    hint: "边界场景：拒答或无依据",
    tag: "边界",
    icon: "🛸",
  },
  { label: "你好", hint: "闲聊分支，不检索知识库", tag: "闲聊", icon: "👋" },
];

interface Props {
  sessionId?: string;
  onSessionChange?: (sessionId: string | undefined) => void;
  onSessionsRefresh?: () => void;
}

export default function ChatPage({ sessionId, onSessionChange, onSessionsRefresh }: Props) {
  const productName = useProductName();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [traces, setTraces] = useState<Record<string, TracePayload>>({});
  const [activeTraceId, setActiveTraceId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runSteps, setRunSteps] = useState<RunStep[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionsRefreshToken, setSessionsRefreshToken] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  const bumpSessions = useCallback(() => {
    setSessionsRefreshToken((t) => t + 1);
    onSessionsRefresh?.();
  }, [onSessionsRefresh]);

  const loadSession = useCallback(async (id: string) => {
    setLoadingHistory(true);
    setError(null);
    try {
      const stored = await fetchSessionMessages(id);
      const mapped: ChatMessage[] = stored.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations?.length ? m.citations : undefined,
        messageId: m.role === "assistant" ? m.id : undefined,
      }));
      const assistantIds = stored.filter((m) => m.role === "assistant").map((m) => m.id);
      const traceEntries = await Promise.all(
        assistantIds.map(async (mid) => {
          try {
            const trace = await fetchTrace(mid);
            return [mid, trace] as const;
          } catch {
            return null;
          }
        }),
      );
      const nextTraces: Record<string, TracePayload> = {};
      for (const entry of traceEntries) {
        if (entry) nextTraces[entry[0]] = entry[1];
      }
      setTraces(nextTraces);
      setMessages(
        mapped.map((m) => {
          if (m.role !== "assistant" || !m.messageId) return m;
          const trace = nextTraces[m.messageId];
          if (!trace?.nodes.length) return m;
          return { ...m, runSteps: traceNodesToRunSteps(trace.nodes) };
        }),
      );
    } catch {
      setError("无法加载对话历史");
      setMessages([]);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      setTraces({});
      return;
    }
    loadSession(sessionId);
  }, [sessionId, loadSession]);

  async function handleSend(question: string) {
    const text = question.trim();
    if (!text || loading) return;

    setError(null);
    setLoading(true);
    setRunSteps([]);
    const tempUserId = crypto.randomUUID();
    const tempAssistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: tempUserId, role: "user", content: text },
      { id: tempAssistantId, role: "assistant", content: "" },
    ]);

    let finalSteps: RunStep[] = [];
    try {
      let streamedAnswer = "";
      const response = await streamChat(text, sessionId, (event) => {
        if (event.type === "node") {
          const step: RunStep = {
            id: `${event.name}-${finalSteps.length}`,
            name: event.name,
            duration_ms: event.duration_ms,
            detail: event.detail,
            status: "running",
          };
          finalSteps = finalSteps.map((s) => ({ ...s, status: "done" as const }));
          finalSteps = [...finalSteps, step];
          setRunSteps(finalSteps);
        }
        if (event.type === "token") {
          streamedAnswer += event.content;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === tempAssistantId ? { ...m, content: streamedAnswer } : m,
            ),
          );
        }
      });
      onSessionChange?.(response.session_id);

      const assistantId = response.message_id;
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserId && m.id !== tempAssistantId),
        { id: tempUserId, role: "user", content: text },
        {
          id: assistantId,
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          messageId: assistantId,
          runSteps: finalSteps.length
            ? finalSteps.map((s) => ({ ...s, status: "done" as const }))
            : undefined,
        },
      ]);

      const traceData = await fetchTrace(assistantId);
      setTraces((prev) => ({ ...prev, [assistantId]: traceData }));
      bumpSessions();
    } catch (err) {
      setMessages((prev) =>
        prev.filter((m) => m.id !== tempUserId && m.id !== tempAssistantId),
      );
      setError(err instanceof Error ? err.message : "请求失败，请确认后端已启动");
    } finally {
      setLoading(false);
      setRunSteps([]);
      setInput("");
      requestAnimationFrame(() => {
        listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
      });
    }
  }

  function handleSelectSession(id: string) {
    onSessionChange?.(id);
    setSidebarOpen(false);
  }

  function handleNewChat() {
    onSessionChange?.(undefined);
    setMessages([]);
    setTraces({});
    setSidebarOpen(false);
  }

  const showHero = messages.length === 0 && !loading && !loadingHistory;
  const activeTrace = activeTraceId ? traces[activeTraceId] : null;

  return (
    <>
      <div className="h-[calc(100vh-60px-28px)] flex max-w-5xl mx-auto w-full">
        <SessionSidebar
          activeSessionId={sessionId}
          refreshToken={sessionsRefreshToken}
          onSelect={handleSelectSession}
          onNew={handleNewChat}
          className="hidden md:flex w-56 lg:w-64 shrink-0"
        />

        {sidebarOpen && (
          <div className="md:hidden fixed inset-0 z-40 flex">
            <button
              type="button"
              className="absolute inset-0 bg-black/30"
              aria-label="关闭"
              onClick={() => setSidebarOpen(false)}
            />
            <SessionSidebar
              activeSessionId={sessionId}
              refreshToken={sessionsRefreshToken}
              onSelect={handleSelectSession}
              onNew={handleNewChat}
              className="relative w-72 max-w-[85vw] h-full z-50 shadow-xl"
            />
          </div>
        )}

        <div className="flex-1 flex flex-col min-w-0">
          <div className="md:hidden px-4 py-2 border-b border-[var(--nc-border)] bg-white/80 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="text-sm text-[var(--nc-navy)] px-3 py-1.5 rounded-lg border border-[var(--nc-border)]"
            >
              历史对话
            </button>
            {sessionId && (
              <span className="text-xs text-[var(--nc-muted)] truncate">当前会话已保存</span>
            )}
          </div>

          <div ref={listRef} className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
            {loadingHistory && (
              <p className="text-center text-sm text-[var(--nc-muted)] py-8">加载对话记录…</p>
            )}

            {showHero && (
              <div className="text-center pt-6 sm:pt-10 pb-8 max-w-lg mx-auto">
                <h2 className="font-display font-bold text-2xl sm:text-3xl text-[var(--nc-navy)] nc-animate-in">
                  有什么可以帮您？
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-8 text-left">
                  {SAMPLE_QUESTIONS.map((item, index) => (
                    <button
                      key={item.label}
                      type="button"
                      disabled={loading}
                      onClick={() => handleSend(item.label)}
                      className="group nc-animate-in text-left p-4 rounded-2xl border border-[var(--nc-border)] bg-white/90 hover:border-[var(--nc-teal)]/50 hover:shadow-[var(--nc-shadow)] transition-all disabled:opacity-50"
                      style={{ animationDelay: `${0.08 + index * 0.07}s` }}
                    >
                      <span className="text-lg" aria-hidden>
                        {item.icon}
                      </span>
                      <p className="text-sm font-medium text-[var(--nc-navy)] mt-2 leading-snug">
                        {item.label}
                      </p>
                      {"hint" in item && item.hint && (
                        <p className="text-xs text-[var(--nc-muted)] mt-1.5 leading-relaxed">{item.hint}</p>
                      )}
                      <span className="inline-block mt-2 text-[10px] tracking-wide text-[var(--nc-muted)] bg-[var(--nc-bg)] px-2 py-0.5 rounded-full">
                        {item.tag}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="max-w-2xl mx-auto space-y-4">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={
                    loading && message.role === "assistant" && !message.content
                      ? { ...message, runSteps: runSteps.length ? runSteps : message.runSteps }
                      : message
                  }
                  onViewProcess={
                    message.messageId && traces[message.messageId]
                      ? () => setActiveTraceId(message.messageId!)
                      : undefined
                  }
                />
              ))}
              {error && (
                <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-xl p-3">
                  {error}
                </p>
              )}
            </div>
          </div>

          <form
            className="shrink-0 p-4 sm:px-6 sm:pb-5 border-t border-[var(--nc-border)] bg-white/70 backdrop-blur-sm"
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(input);
            }}
          >
            <div className="max-w-2xl mx-auto flex gap-2 p-1.5 rounded-2xl border border-[var(--nc-border)] bg-white shadow-[var(--nc-shadow)] focus-within:ring-2 focus-within:ring-[var(--nc-teal)]/30">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="继续追问…"
                className="flex-1 bg-transparent px-4 py-2.5 text-sm outline-none"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="shrink-0 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[var(--nc-navy)] to-[var(--nc-navy-deep)] text-white text-sm font-medium disabled:opacity-40"
              >
                发送
              </button>
            </div>
          </form>
        </div>
      </div>

      {activeTrace && (
        <TraceDrawer
          trace={activeTrace}
          open={Boolean(activeTraceId)}
          onClose={() => setActiveTraceId(null)}
        />
      )}
    </>
  );
}
