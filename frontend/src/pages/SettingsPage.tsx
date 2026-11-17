import { useEffect, useState } from "react";
import { fetchSettings, updateSettings } from "../api/client";
import type { AssistantSettings } from "../api/types";
import { distanceToStrictness, strictnessToDistance } from "../lib/labels";
import { useAssistant } from "../context/AssistantContext";

export default function SettingsPage() {
  const { refreshSettings } = useAssistant();
  const [form, setForm] = useState<AssistantSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [strictness, setStrictness] = useState(3);

  useEffect(() => {
    fetchSettings()
      .then((data) => {
        setForm(data);
        setStrictness(distanceToStrictness(data.max_retrieval_distance));
      })
      .catch(() => setMessage("无法加载设定，请确认后端已启动"));
  }, []);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!form) return;

    setSaving(true);
    setMessage(null);
    try {
      const payload = {
        ...form,
        max_retrieval_distance: strictnessToDistance(strictness),
      };
      await updateSettings(payload);
      await refreshSettings();
      setForm(payload);
      setMessage("已保存，下一次提问起生效");
    } catch {
      setMessage("保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  }

  if (!form) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center text-[var(--nc-muted)] text-sm">
        {message ?? "加载助手设定…"}
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
      <div className="nc-animate-in mb-8">
        <h2 className="font-display font-bold text-2xl text-[var(--nc-navy)]">助手设定</h2>
        <p className="text-sm text-[var(--nc-muted)] mt-2 leading-relaxed">
          在此调整助手行为，保存后立即生效，无需改代码或重启服务。
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6 nc-animate-in">
        <label className="block">
          <span className="text-sm font-medium text-[var(--nc-navy)]">产品名称</span>
          <p className="text-xs text-[var(--nc-muted)] mt-1 mb-2">显示在顶栏，并用于 AI 自我介绍</p>
          <input
            value={form.product_name}
            onChange={(e) => setForm({ ...form, product_name: e.target.value })}
            className="w-full border border-[var(--nc-border)] rounded-xl px-4 py-2.5 text-sm bg-white focus:ring-2 focus:ring-[var(--nc-teal)]/30 outline-none"
            maxLength={32}
            required
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-[var(--nc-navy)]">检索范围</span>
          <p className="text-xs text-[var(--nc-muted)] mt-1 mb-2">
            auto 时由分类自动选择；也可强制只查架构或业务文档
          </p>
          <select
            value={form.retrieval_scope}
            onChange={(e) =>
              setForm({
                ...form,
                retrieval_scope: e.target.value as AssistantSettings["retrieval_scope"],
              })
            }
            className="w-full border border-[var(--nc-border)] rounded-xl px-4 py-2.5 text-sm bg-white focus:ring-2 focus:ring-[var(--nc-teal)]/30 outline-none"
          >
            <option value="auto">自动（跟随分类）</option>
            <option value="all">全部文档</option>
            <option value="arch_only">仅架构文档</option>
            <option value="business_only">仅业务文档</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-medium text-[var(--nc-navy)]">
            每次查找资料条数：{form.retrieve_top_k}
          </span>
          <p className="text-xs text-[var(--nc-muted)] mt-1 mb-2">条数越多越全面，但可能更慢</p>
          <input
            type="range"
            min={4}
            max={20}
            value={form.retrieve_top_k}
            onChange={(e) => setForm({ ...form, retrieve_top_k: Number(e.target.value) })}
            className="w-full accent-[var(--nc-teal)]"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-[var(--nc-navy)]">
            回答严格程度：{strictness}/5
          </span>
          <p className="text-xs text-[var(--nc-muted)] mt-1 mb-2">
            越高越谨慎，资料不够相关时更容易提示「暂未找到」
          </p>
          <input
            type="range"
            min={1}
            max={5}
            value={strictness}
            onChange={(e) => setStrictness(Number(e.target.value))}
            className="w-full accent-[var(--nc-navy)]"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-[var(--nc-navy)]">
            改写重试次数：{form.max_rewrite_retries}
          </span>
          <p className="text-xs text-[var(--nc-muted)] mt-1 mb-2">
            检索不理想时自动改写问题再查，0 表示不重试
          </p>
          <input
            type="range"
            min={0}
            max={3}
            value={form.max_rewrite_retries}
            onChange={(e) => setForm({ ...form, max_rewrite_retries: Number(e.target.value) })}
            className="w-full accent-[var(--nc-teal)]"
          />
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={form.enable_llm_grade}
            onChange={(e) => setForm({ ...form, enable_llm_grade: e.target.checked })}
            className="rounded border-[var(--nc-border)] accent-[var(--nc-navy)]"
          />
          <span className="text-sm text-[var(--nc-navy)]">边界情况用 AI 判断资料是否有用</span>
        </label>

        <label className="block">
          <span className="text-sm font-medium text-[var(--nc-navy)]">找不到资料时的提示语</span>
          <textarea
            value={form.refuse_message}
            onChange={(e) => setForm({ ...form, refuse_message: e.target.value })}
            rows={3}
            className="w-full mt-2 border border-[var(--nc-border)] rounded-xl px-4 py-2.5 text-sm bg-white focus:ring-2 focus:ring-[var(--nc-teal)]/30 outline-none resize-none"
            maxLength={500}
            required
          />
        </label>

        {message && (
          <p
            className={`text-sm rounded-xl p-3 ${
              message.includes("失败")
                ? "text-red-700 bg-red-50 border border-red-100"
                : "text-[var(--nc-navy)] bg-[var(--nc-teal)]/10 border border-[var(--nc-teal)]/20"
            }`}
          >
            {message}
          </p>
        )}

        <button
          type="submit"
          disabled={saving}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-[var(--nc-navy)] to-[var(--nc-navy-deep)] text-white text-sm font-medium hover:opacity-95 disabled:opacity-50"
        >
          {saving ? "保存中…" : "保存并应用"}
        </button>
      </form>

      <section className="mt-10 pt-8 border-t border-[var(--nc-border)] nc-animate-in">
        <h3 className="font-display font-semibold text-lg text-[var(--nc-navy)]">模型与依赖</h3>
        <p className="text-xs text-[var(--nc-muted)] mt-2 mb-4 leading-relaxed">
          只读说明，便于对照本仓库实现；密钥请在项目根目录 <code className="font-mono-nc">.env</code> 配置。
        </p>
        <dl className="text-sm space-y-3 rounded-xl border border-[var(--nc-border)] bg-white p-4">
          <div>
            <dt className="font-medium text-[var(--nc-navy)]">对话 / 分类 / 生成 / 改写</dt>
            <dd className="text-[var(--nc-muted)] text-xs mt-0.5">DeepSeek API（DEEPSEEK_API_KEY）</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--nc-navy)]">向量 Embedding</dt>
            <dd className="text-[var(--nc-muted)] text-xs mt-0.5">Ollama nomic-embed-text（本地 HTTP）</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--nc-navy)]">编排</dt>
            <dd className="text-[var(--nc-muted)] text-xs mt-0.5">LangGraph（classify → retrieve → grade → …）</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--nc-navy)]">检索与入库</dt>
            <dd className="text-[var(--nc-muted)] text-xs mt-0.5">LangChain + ChromaDB，知识库含 data/arch/ 自指文档</dd>
          </div>
        </dl>
      </section>

      <p className="text-[11px] text-[var(--nc-muted)] mt-8 leading-relaxed">
        严格程度对应向量匹配阈值；API 密钥不在此页修改。
      </p>
    </div>
  );
}
