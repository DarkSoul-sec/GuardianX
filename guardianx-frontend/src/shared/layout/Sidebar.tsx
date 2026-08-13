import { X } from "lucide-react";
import { NavLink } from "react-router-dom";

import {
  LayoutDashboard,
  Server,
  ShieldAlert,
  ScanSearch,
  FileText,
  Settings,
  Bot,
  Radar,
  Fish,
  Crosshair,
  Swords,
  ShieldHalf,
  AlarmSmoke,
  Siren,
  ScrollText,
} from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

const menu = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    path: "/",
  },
  {
    title: "Assets",
    icon: Server,
    path: "/assets",
  },
  {
    title: "Findings",
    icon: ShieldAlert,
    path: "/findings",
  },
  {
    title: "Scans",
    icon: ScanSearch,
    path: "/scans",
  },
  {
    title: "Reports",
    icon: FileText,
    path: "/reports",
  },
  {
    title: "AI Security Copilot",
    icon: Bot,
    path: "/copilot",
  },
  {
    title: "VirusTotal",
    icon: Radar,
    path: "/virustotal",
  },
  {
    title: "Phishing",
    icon: Fish,
    path: "/phishing",
  },
  {
    title: "Threat Intel",
    icon: Crosshair,
    path: "/threat-intel",
  },
  {
    title: "Threat Intelligence",
    icon: Swords,
    path: "/intelligence",
  },
  {
    title: "Security Operations",
    icon: ShieldHalf,
    path: "/soc",
  },
  {
    title: "Alert Center",
    icon: AlarmSmoke,
    path: "/alerts",
  },
  {
    title: "Incidents",
    icon: Siren,
    path: "/incidents",
  },
  {
    title: "Activity Log",
    icon: ScrollText,
    path: "/activity",
  },
  {
    title: "Settings",
    icon: Settings,
    path: "/settings",
  },
];

function SidebarContent({ onNavigate }: { onNavigate: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="relative overflow-hidden border-b border-slate-800/70">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent" />
        <div className="relative flex items-center justify-between p-8">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-[0.18em] neon-text glow-text">
              GuardianX
            </h1>
            <p className="eyebrow mt-2">AI Security Platform</p>
          </div>
          <button
            onClick={onNavigate}
            aria-label="Close menu"
            className="rounded-lg border border-slate-800 bg-slate-900/60 p-2 text-slate-400 transition hover:border-cyan-500/40 hover:text-cyan-300 lg:hidden"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      <nav className="space-y-1.5 overflow-y-auto p-5">
        {menu.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onNavigate}
              className={({ isActive }) =>
                `group relative flex items-center gap-4 overflow-hidden rounded-xl px-4 py-3 text-sm font-semibold tracking-wide transition ${
                  isActive
                    ? "bg-cyan-500/10 text-cyan-300 shadow-[inset_0_0_24px_rgba(0,207,255,0.12)]"
                    : "text-slate-300 hover:bg-slate-800/60 hover:text-cyan-200"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r bg-cyan-400 shadow-[0_0_12px_rgba(0,207,255,0.9)]" />
                  )}
                  <Icon
                    size={20}
                    className={isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-cyan-300"}
                  />
                  {item.title}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-auto border-t border-slate-800/70 p-5">
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-600">
          GuardianX OS v2.6
        </p>
      </div>
    </div>
  );
}

export default function Sidebar({ open, onClose }: Props) {
  return (
    <>
      <aside className="hidden w-72 shrink-0 border-r border-slate-800/70 bg-slate-950/50 backdrop-blur-xl lg:block">
        <SidebarContent onNavigate={onClose} />
      </aside>

      {open && (
        <div className="fixed inset-0 z-50 lg:hidden" onClick={onClose}>
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
          <aside
            className="absolute left-0 h-full w-72 border-r border-slate-800/70 bg-slate-950/90 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <SidebarContent onNavigate={onClose} />
          </aside>
        </div>
      )}
    </>
  );
}
