import { LogOut, Menu, UserCircle2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import SearchInput from "@/shared/components/SearchInput";
import NotificationBell from "@/components/notifications/NotificationBell";
import { useMe } from "@/hooks/useUsers";
import { useAuth } from "@/hooks/useAuth";

const roleStyles: Record<string, string> = {
  ADMIN: "bg-red-500/15 text-red-400",
  SECURITY_ENGINEER: "bg-cyan-500/15 text-cyan-400",
  ANALYST: "bg-blue-500/15 text-blue-400",
  VIEWER: "bg-slate-500/15 text-slate-400",
  USER: "bg-green-500/15 text-green-400",
};

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const { data } = useMe();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const [query, setQuery] = useState("");

  function handleSearchSubmit(event: FormEvent) {
    event.preventDefault();
    const term = query.trim();
    if (!term) return;
    navigate(`/findings?q=${encodeURIComponent(term)}`);
    setQuery("");
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="flex min-h-20 flex-wrap items-center justify-between gap-3 border-b border-slate-800/70 bg-slate-950/40 px-4 py-3 backdrop-blur-xl md:px-8 md:py-0">
      <div className="flex w-full items-center gap-3 md:w-auto md:flex-1">
        <button
          onClick={onMenuClick}
          aria-label="Open menu"
          title="Open menu"
          className="rounded-lg p-2 text-slate-300 transition hover:bg-slate-800 hover:text-white lg:hidden"
        >
          <Menu size={20} />
        </button>
        <form onSubmit={handleSearchSubmit} className="w-full max-w-sm" role="search">
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search assets, CVEs..."
            ariaLabel="Search findings"
          />
        </form>
      </div>

      <div className="flex items-center gap-4 md:gap-6">
        <NotificationBell />

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 rounded-xl border border-slate-700/70 bg-slate-900/70 px-4 py-2 backdrop-blur-sm">
            <UserCircle2 size={24} className="text-cyan-400" />
            <div className="leading-tight">
              <p className="text-sm font-semibold text-white">
                {data?.username ?? "User"}
              </p>
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-bold ${
                  roleStyles[data?.role ?? "USER"] ?? roleStyles.USER
                }`}
              >
                {data?.role ?? "USER"}
              </span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            aria-label="Log out"
            title="Log out"
            className="rounded-lg bg-slate-800 p-3 text-slate-300 transition hover:bg-red-600 hover:text-white"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
  );
}
