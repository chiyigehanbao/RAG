import { useState } from "react";
import type { ReactNode } from "react";
import { BrowserRouter, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import Logo from "./components/Logo";
import { AssistantProvider, useProductName } from "./context/AssistantContext";
import ChatPage from "./pages/ChatPage";
import DocumentsPage from "./pages/DocumentsPage";
import SettingsPage from "./pages/SettingsPage";

function NavItem({ to, children }: { to: string; children: ReactNode }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? "bg-[var(--nc-navy)]/8 text-[var(--nc-navy)]"
            : "text-[var(--nc-muted)] hover:text-[var(--nc-navy)] hover:bg-white/60"
        }`
      }
    >
      {children}
    </NavLink>
  );
}

function AppShell() {
  const navigate = useNavigate();
  const productName = useProductName();
  const [chatKey, setChatKey] = useState(0);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>();

  function startNewChat() {
    setActiveSessionId(undefined);
    setChatKey((k) => k + 1);
    navigate("/");
  }

  return (
    <div className="min-h-full flex flex-col nc-page-bg">
      <header className="sticky top-0 z-20 border-b border-[var(--nc-border)]/80 bg-white/85 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-[60px] flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={startNewChat}
            className="flex items-center gap-3 min-w-0 text-left hover:opacity-90 transition-opacity"
          >
            <Logo size="sm" />
            <div className="min-w-0">
              <p className="font-display font-semibold text-[var(--nc-navy)] text-base leading-tight truncate">
                {productName}
              </p>
              <p className="text-[11px] text-[var(--nc-muted)] truncate">知识库助手</p>
            </div>
          </button>

          <nav className="flex items-center gap-0.5">
            <NavItem to="/">对话</NavItem>
            <NavItem to="/documents">文档</NavItem>
            <NavItem to="/settings">助手设定</NavItem>
          </nav>
        </div>
      </header>

      <main className="flex-1 min-h-0">
        <Routes>
          <Route
            path="/"
            element={
              <ChatPage
                key={chatKey}
                sessionId={activeSessionId}
                onSessionChange={setActiveSessionId}
              />
            }
          />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>

      <footer className="shrink-0 py-2 text-center text-[10px] text-[var(--nc-muted)]/80 border-t border-[var(--nc-border)]/50 bg-white/40">
        对话保存在本地数据库 · 支持多轮上下文
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AssistantProvider>
        <AppShell />
      </AssistantProvider>
    </BrowserRouter>
  );
}
