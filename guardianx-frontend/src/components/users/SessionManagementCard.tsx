import { useState } from "react";
import { LogOut, Monitor, ShieldAlert, Smartphone } from "lucide-react";

import { Button } from "@/shared/components";
import { Card } from "@/shared/components";
import {
  useRevokeAllSessions,
  useRevokeSession,
  useSessions,
} from "@/hooks/useUsers";
import { useToastContext } from "@/hooks/useToastContext";

function deviceIcon(userAgent: string | null) {
  const agent = (userAgent ?? "").toLowerCase();

  if (agent.includes("iphone") || agent.includes("ipad")) return <Smartphone size={16} />;
  if (agent.includes("android")) return <Smartphone size={16} />;
  return <Monitor size={16} />;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

export default function SessionManagementCard() {
  const { data: sessions, isLoading } = useSessions();
  const revokeSession = useRevokeSession();
  const revokeAll = useRevokeAllSessions();
  const { success, error } = useToastContext();
  const [confirmAll, setConfirmAll] = useState(false);

  function handleRevoke(id: number) {
    revokeSession.mutate(id, {
      onSuccess: () => success("Session signed out."),
      onError: () => error("Failed to revoke session."),
    });
  }

  function handleRevokeAll() {
    revokeAll.mutate(undefined, {
      onSuccess: () => {
        success("All sessions were signed out.");
        setConfirmAll(false);
      },
      onError: () => error("Failed to revoke sessions."),
    });
  }

  return (
    <Card className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Active Sessions</h2>
          <p className="mt-1 text-sm text-slate-400">
            Devices currently signed in to your account.
          </p>
        </div>
        {sessions && sessions.length > 0 && !confirmAll && (
          <button
            type="button"
            className="text-sm text-slate-400 underline-offset-2 hover:text-cyan-300 hover:underline"
            onClick={() => setConfirmAll(true)}
          >
            Sign out all
          </button>
        )}
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading sessions...</p>
      ) : !sessions || sessions.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 p-8 text-center text-sm text-slate-500">
          You have no active sessions.
        </div>
      ) : (
        <ul className="divide-y divide-slate-800">
          {sessions.map((session) => (
            <li
              key={session.id}
              className="flex items-center justify-between gap-4 py-4"
            >
              <div className="flex items-center gap-3">
                <span className="text-cyan-400">{deviceIcon(session.user_agent)}</span>
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    {session.user_agent
                      ? session.user_agent.slice(0, 64)
                      : "Unknown device"}
                    {session.user_agent && session.user_agent.length > 64 ? "…" : ""}
                  </p>
                  <p className="text-xs text-slate-500">
                    Signed in {formatDate(session.created_at)}
                    {session.ip_address ? ` · ${session.ip_address}` : ""}
                  </p>
                </div>
              </div>
              <Button
                variant="secondary"
                type="button"
                onClick={() => handleRevoke(session.id)}
                disabled={revokeSession.isPending}
              >
                <LogOut size={14} /> Sign out
              </Button>
            </li>
          ))}
        </ul>
      )}

      {confirmAll && (
        <div className="mt-4 flex items-center gap-3 rounded-xl border border-red-800/50 bg-red-950/30 p-4">
          <ShieldAlert className="text-red-400" size={18} />
          <p className="flex-1 text-sm text-slate-300">
            Sign out of all active sessions?
          </p>
          <Button variant="danger" onClick={handleRevokeAll} disabled={revokeAll.isPending}>
            {revokeAll.isPending ? "Signing out..." : "Confirm"}
          </Button>
          <Button variant="secondary" onClick={() => setConfirmAll(false)}>
            Cancel
          </Button>
        </div>
      )}
    </Card>
  );
}