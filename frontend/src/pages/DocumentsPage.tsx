import { useCallback, useEffect, useState } from "react";
import { fetchDocuments, reindexDocuments, uploadDocument } from "../api/client";
import type { DocumentItem } from "../api/types";
import DocumentTable from "../components/DocumentTable";
import UploadZone from "../components/UploadZone";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [reindexing, setReindexing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchDocuments();
      setDocuments(data);
    } catch {
      setError("无法加载文档列表，请确认后端已启动");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleReindex() {
    setReindexing(true);
    setMessage(null);
    setError(null);
    try {
      const result = await reindexDocuments();
      setMessage(`全库重新索引完成，共 ${result.chunks_indexed} 个片段`);
      await load();
    } catch {
      setError("重新索引失败，请检查 Ollama 与 Chroma 是否可用");
    } finally {
      setReindexing(false);
    }
  }

  async function handleUpload(file: File) {
    setError(null);
    setMessage(null);
    try {
      const result = await uploadDocument(file);
      setMessage(`已入库「${result.path}」，共 ${result.chunks_indexed} 个片段，可直接在对话中提问`);
      await load();
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(typeof detail === "string" ? detail : "上传失败，请确认后端已启动且 Ollama 可用");
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-8">
      <div className="nc-animate-in flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h2 className="font-display font-bold text-2xl text-[var(--nc-navy)]">知识库文档</h2>
          <p className="text-sm text-[var(--nc-muted)] mt-2 leading-relaxed">
            上传 Markdown 保存至 <code className="text-xs font-mono-nc bg-white px-1 rounded border">data/uploads/</code>
            并增量入库；「重新索引」会重建整个向量库。
          </p>
        </div>
        <button
          type="button"
          onClick={handleReindex}
          disabled={reindexing}
          className="shrink-0 px-5 py-2.5 rounded-xl border-2 border-[var(--nc-border)] text-[var(--nc-navy)] text-sm font-medium hover:bg-[var(--nc-bg)] disabled:opacity-50"
        >
          {reindexing ? "索引中…" : "重新索引全库"}
        </button>
      </div>

      <UploadZone disabled={reindexing} onUpload={handleUpload} />

      {message && (
        <p className="text-sm text-[var(--nc-navy)] bg-[var(--nc-teal)]/10 border border-[var(--nc-teal)]/30 rounded-xl p-4 nc-animate-in">
          {message}
        </p>
      )}
      {error && (
        <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-xl p-4">{error}</p>
      )}

      <DocumentTable documents={documents} loading={loading} />
    </div>
  );
}
