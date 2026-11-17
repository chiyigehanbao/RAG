import axios from "axios";
import type {
  AssistantSettings,
  ChatResponse,
  DocumentChunk,
  DocumentItem,
  SessionSummary,
  StoredMessage,
  StreamEvent,
  TracePayload,
} from "./types";

const api = axios.create({ baseURL: "/api" });

export async function sendChat(question: string, sessionId?: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/chat", {
    question,
    session_id: sessionId,
  });
  return data;
}

export async function fetchTrace(messageId: string): Promise<TracePayload> {
  const { data } = await api.get<TracePayload>(`/traces/${messageId}`);
  return data;
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const { data } = await api.get<DocumentItem[]>("/documents");
  return data;
}

export async function reindexDocuments(
  source = "./data",
): Promise<{ status: string; chunks_indexed: number }> {
  const { data } = await api.post("/documents/reindex", { source });
  return data;
}

export async function fetchSettings(): Promise<AssistantSettings> {
  const { data } = await api.get<AssistantSettings>("/settings");
  return data;
}

export async function updateSettings(
  patch: Partial<AssistantSettings>,
): Promise<AssistantSettings> {
  const { data } = await api.put<AssistantSettings>("/settings", patch);
  return data;
}

export async function fetchSessions(): Promise<SessionSummary[]> {
  const { data } = await api.get<SessionSummary[]>("/sessions");
  return data;
}

export async function fetchSessionMessages(sessionId: string): Promise<StoredMessage[]> {
  const { data } = await api.get<StoredMessage[]>(`/sessions/${sessionId}/messages`);
  return data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/sessions/${sessionId}`, {
    validateStatus: (status) => status === 204 || status === 200,
  });
}

export async function streamChat(
  question: string,
  sessionId: string | undefined,
  onEvent: (event: StreamEvent) => void,
): Promise<ChatResponse> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  });

  if (!response.ok || !response.body) {
    throw new Error("流式请求失败，请确认后端已启动");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: ChatResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = JSON.parse(line.slice(6)) as StreamEvent;
      onEvent(payload);
      if (payload.type === "done" && "message_id" in payload) {
        result = {
          message_id: payload.message_id,
          session_id: payload.session_id,
          trace_id: payload.trace_id,
          answer: payload.answer,
          citations: payload.citations,
        };
      }
      if (payload.type === "error") {
        throw new Error(payload.message);
      }
    }
  }

  if (!result) {
    throw new Error("未收到完整响应");
  }
  return result;
}

export async function fetchDocumentChunks(path: string): Promise<DocumentChunk[]> {
  const { data } = await api.get<DocumentChunk[]>("/documents/chunks", { params: { path } });
  return data;
}

export async function uploadDocument(
  file: File,
): Promise<{ status: string; path: string; chunks_indexed: number }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
