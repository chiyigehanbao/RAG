/** 面向普通用户的前端文案与来源友好名映射 */

const SOURCE_LABELS: Record<string, string> = {
  "arch/overview.md": "项目总览",
  "arch/langgraph-flow.md": "LangGraph 流程",
  "arch/rag-pipeline.md": "RAG 流水线",
  "arch/langchain-usage.md": "LangChain 用法",
  "arch/config.md": "配置说明",
  "arch/faq.md": "架构 FAQ",
  "faq/account.md": "账号与计费常见问题",
  "faq/troubleshooting.md": "故障排查指南",
  "wiki/billing.md": "计费与套餐说明",
  "wiki/deployment.md": "部署与上线",
  "wiki/permissions.md": "权限与角色",
  "product_manual/overview.md": "产品概览",
  "product_manual/features.md": "功能说明",
  "product_manual/integrations.md": "集成与对接",
};

/** 将存储路径转为可读文档名 */
export function friendlySource(path: string): string {
  if (SOURCE_LABELS[path]) return SOURCE_LABELS[path];
  const name = path.split("/").pop()?.replace(/\.md$/i, "") ?? path;
  return name.replace(/[-_]/g, " ");
}

/** 引用展示：文档名 · 章节 */
export function formatCitation(source: string, section: string): string {
  return `${friendlySource(source)} · ${section}`;
}

export const ROUTE_LABELS: Record<string, string> = {
  need_rag: "查阅知识库",
  no_rag: "直接回复",
};

export const NODE_LABELS: Record<string, string> = {
  classify: "理解问题",
  retrieve: "查找资料",
  grade: "判断资料是否有用",
  rewrite: "改写问题再查",
  generate: "组织回答",
  refuse: "礼貌说明",
  chitchat: "轻松闲聊",
};

const GRADE_REASON_LABELS: Record<string, string> = {
  ok: "资料足够相关",
  empty: "未找到资料",
  distance: "相似度偏低",
  llm: "智能判定：可用",
  llm_reject: "智能判定：不够用",
};

/** 严格度 1–5 与后端 max_retrieval_distance 互转 */
export function strictnessToDistance(level: number): number {
  const map: Record<number, number> = { 1: 600, 2: 500, 3: 450, 4: 350, 5: 250 };
  return map[level] ?? 450;
}

export function gradeReasonLabel(reason: string | undefined): string {
  if (!reason) return "";
  return GRADE_REASON_LABELS[reason] ?? reason;
}

export function distanceToStrictness(distance: number): number {
  if (distance >= 550) return 1;
  if (distance >= 480) return 2;
  if (distance >= 400) return 3;
  if (distance >= 300) return 4;
  return 5;
}
