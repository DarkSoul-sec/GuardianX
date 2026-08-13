import { useEffect, useState, type FormEvent, type KeyboardEvent } from "react";
import { Plug, Radar, User, Lock } from "lucide-react";

import {
  Button,
  Card,
  Input,
  PageHeader,
  Skeleton,
} from "@/shared/components";

import VirusTotalSettingsCard from "@/components/virustotal/VirusTotalSettingsCard";
import ScanPreferencesCard from "@/components/scans/ScanPreferencesCard";
import SessionManagementCard from "@/components/users/SessionManagementCard";

import { useChangePassword, useMe, useUpdateProfile } from "@/hooks/useUsers";
import { useToastContext } from "@/hooks/useToastContext";

type Tab = "profile" | "security" | "scanning" | "integrations";

export default function Settings() {
  const [tab, setTab] = useState<Tab>("profile");
  const { data, isLoading } = useMe();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [initialized, setInitialized] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const updateProfile = useUpdateProfile();
  const changePassword = useChangePassword();
  const { success, error } = useToastContext();

  useEffect(() => {
    if (!initialized && data) {
      setUsername(data.username);
      setEmail(data.email ?? "");
      setInitialized(true);
    }
  }, [initialized, data]);

  function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
    updateProfile.mutate(
      { username, email: email.trim() || null },
      {
        onSuccess: () => success("Profile updated successfully."),
        onError: () => error("Failed to update profile."),
      }
    );
  }

  function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      error("New passwords do not match.");
      return;
    }
    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          success("Password changed successfully.");
          setCurrentPassword("");
          setNewPassword("");
          setConfirmPassword("");
        },
        onError: (err) => {
          error(
            err instanceof Error && err.message
              ? err.message
              : "Failed to change password."
          );
        },
      }
    );
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "profile", label: "Profile", icon: <User size={16} /> },
    { id: "security", label: "Security", icon: <Lock size={16} /> },
    { id: "scanning", label: "Scanning", icon: <Radar size={16} /> },
    { id: "integrations", label: "Integrations", icon: <Plug size={16} /> },
  ];

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, id: Tab) {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;

    event.preventDefault();
    const currentIndex = tabs.findIndex((tab) => tab.id === id);
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const next = tabs[(currentIndex + direction + tabs.length) % tabs.length];
    setTab(next.id);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Manage your account and platform preferences"
      />

      <div
        role="tablist"
        aria-label="Settings sections"
        className="flex gap-2 rounded-xl border border-slate-800 bg-slate-900 p-2"
      >
        {tabs.map((item) => (
          <button
            key={item.id}
            id={`settings-tab-${item.id}`}
            role="tab"
            aria-selected={tab === item.id}
            aria-controls={`settings-panel-${item.id}`}
            tabIndex={tab === item.id ? 0 : -1}
            onClick={() => setTab(item.id)}
            onKeyDown={(e) => handleTabKeyDown(e, item.id)}
            className={`flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition ${
              tab === item.id
                ? "bg-cyan-600 text-white"
                : "text-slate-400 hover:bg-slate-800 hover:text-white"
            }`}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <div
          id="settings-panel-active"
          role="tabpanel"
          aria-labelledby={`settings-tab-${tab}`}
          className="max-w-2xl"
        >
          {tab === "profile" && (
            <Card className="p-8">
              <h2 className="mb-6 text-2xl font-bold text-white">Profile</h2>
              <form onSubmit={handleProfileSubmit} className="space-y-5">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Username
                  </label>
                  <Input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    minLength={3}
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Email <span className="font-normal text-slate-500">(optional)</span>
                  </label>
                  <Input
                    type="email"
                    value={email ?? ""}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
                  <span className="font-semibold text-slate-300">Role:</span>{" "}
                  {data?.role ?? "USER"}
                </div>

                <Button type="submit" disabled={updateProfile.isPending}>
                  {updateProfile.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </form>
            </Card>
          )}

          {tab === "security" && (
            <Card className="p-8">
              <h2 className="mb-2 text-2xl font-bold text-white">
                Change Password
              </h2>
              <p className="mb-6 text-sm text-slate-400">
                Passwords must be at least 12 characters.
              </p>
              <form onSubmit={handlePasswordSubmit} className="space-y-5">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Current Password
                  </label>
                  <Input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    New Password
                  </label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={12}
                    autoComplete="new-password"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Confirm New Password
                  </label>
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={12}
                    autoComplete="new-password"
                  />
                </div>

                <Button type="submit" disabled={changePassword.isPending}>
                  {changePassword.isPending ? "Updating..." : "Update Password"}
                </Button>
              </form>
            </Card>
          )}

          {tab === "security" && (
            <div className="space-y-6">
              <SessionManagementCard />
            </div>
          )}
          {tab === "scanning" && <ScanPreferencesCard />}
          {tab === "integrations" && (
            <div className="space-y-6">
              <VirusTotalSettingsCard />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
