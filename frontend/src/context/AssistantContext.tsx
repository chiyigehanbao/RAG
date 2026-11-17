import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { fetchSettings } from "../api/client";
import type { AssistantSettings } from "../api/types";

interface AssistantContextValue {
  settings: AssistantSettings | null;
  loading: boolean;
  refreshSettings: () => Promise<void>;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

const DEFAULT_SETTINGS: AssistantSettings = {
  product_name: "RAG 架构助手",
  retrieve_top_k: 10,
  max_retrieval_distance: 450,
  refuse_message: "暂未在知识库中找到相关资料，建议联系管理员或提交工单。",
  max_rewrite_retries: 2,
  enable_llm_grade: true,
  grade_margin: 80,
};

export function AssistantProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AssistantSettings | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshSettings = useCallback(async () => {
    try {
      const data = await fetchSettings();
      setSettings(data);
    } catch {
      setSettings(DEFAULT_SETTINGS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSettings();
  }, [refreshSettings]);

  const value = useMemo(
    () => ({ settings, loading, refreshSettings }),
    [settings, loading, refreshSettings],
  );

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistant() {
  const ctx = useContext(AssistantContext);
  if (!ctx) throw new Error("useAssistant must be used within AssistantProvider");
  return ctx;
}

export function useProductName(): string {
  const { settings } = useAssistant();
  return settings?.product_name ?? DEFAULT_SETTINGS.product_name;
}
