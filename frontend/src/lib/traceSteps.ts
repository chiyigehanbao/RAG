import type { TraceNode } from "../api/types";
import type { RunStep } from "../api/types";

function nodeDetail(node: TraceNode): Record<string, unknown> | undefined {
  const out = node.output;
  if (node.name === "classify") return { route: out.route };
  if (node.name === "retrieve") {
    return { top_k: out.top_k, min_distance: out.min_distance };
  }
  if (node.name === "grade") {
    return {
      grade_reason: out.grade_reason,
      min_distance: out.min_distance,
      is_relevant: out.is_relevant,
    };
  }
  if (node.name === "rewrite") {
    const inp = node.input;
    return {
      rewritten_query: out.rewritten_query,
      retry_count: out.retry_count,
      last_query: inp.last_query ?? inp.original_query,
    };
  }
  return undefined;
}

/** 将持久化 trace 转为对话页执行链路展示 */
export function traceNodesToRunSteps(nodes: TraceNode[]): RunStep[] {
  return nodes.map((node, index) => ({
    id: `${node.name}-${index}`,
    name: node.name,
    duration_ms: node.duration_ms,
    detail: nodeDetail(node),
    status: "done",
  }));
}
