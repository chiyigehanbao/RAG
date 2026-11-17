import { useRef, useState } from "react";

interface Props {
  disabled?: boolean;
  onUpload: (file: File) => Promise<void>;
}

/** Markdown 拖拽/选择上传区 */
export default function UploadZone({ disabled, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);

  async function handleFile(file: File | undefined) {
    if (!file || disabled || uploading) return;
    if (!file.name.toLowerCase().endsWith(".md")) {
      window.alert("仅支持 .md 文件");
      return;
    }
    setUploading(true);
    try {
      await onUpload(file);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files[0]);
      }}
      onClick={() => !disabled && !uploading && inputRef.current?.click()}
      className={`relative rounded-2xl border-2 border-dashed p-8 text-center transition-colors cursor-pointer ${
        dragOver
          ? "border-[var(--nc-teal)] bg-[var(--nc-teal)]/5"
          : "border-[var(--nc-border)] bg-white/60 hover:border-[var(--nc-teal)]/40"
      } ${disabled || uploading ? "opacity-50 pointer-events-none" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".md,text/markdown"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <div className="text-3xl mb-3" aria-hidden>
        📄
      </div>
      <p className="text-sm font-medium text-[var(--nc-navy)]">
        {uploading ? "正在上传并入库…" : "拖拽 Markdown 到此处，或点击选择"}
      </p>
      <p className="text-xs text-[var(--nc-muted)] mt-2">仅 .md，单文件不超过 512KB</p>
    </div>
  );
}
