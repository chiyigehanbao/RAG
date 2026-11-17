export interface Citation {
  source: string;
  section: string;
}

export interface ChatResponse {
  message_id: string;
  session_id: string;
  answer: string;
  citations: Citation[];
  trace_id: string;
}

export interface TraceNode {
  name: string;
  duration_ms: number;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
}

export interface TracePayload {
  message_id: string;
  question: string;
  nodes: TraceNode[];
  citations: Citation[];
}

export interface DocumentItem {
  id: string;
  path: string;
  status: string;
  chunk_count: number;
}

export interface DocumentChunk {
  index: number;
  section: string;
  char_count: number;
  preview: string;
}

export interface RunStep {
  id: string;
  name: string;
  duration_ms: number;
  detail?: Record<string, unknown>;
  status: "running" | "done";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  messageId?: string;
  /** 本条助手回复对应的 LangGraph 节点（回答完成后保留展示） */
  runSteps?: RunStep[];
}

export interface RetrieveChunk {
  content: string;
  source: string;
  section: string;
  score: number;
  distance?: number;
}

export interface AssistantSettings {
  product_name: string;
  retrieve_top_k: number;
  max_retrieval_distance: number;
  refuse_message: string;
  max_rewrite_retries: number;
  enable_llm_grade: boolean;
  grade_margin: number;
  retrieval_scope: "auto" | "all" | "arch_only" | "business_only";
}

export interface SessionSummary {
  id: string;
  title: string;
  created_at: string;
}

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  citations: Citation[];
}

export type StreamEvent =
  | { type: "node"; name: string; duration_ms: number; detail?: Record<string, unknown> }
  | { type: "token"; content: string }
  | {
      type: "done";
      message_id: string;
      session_id: string;
      trace_id: string;
      answer: string;
      citations: Citation[];
    }
  | { type: "error"; message: string };
