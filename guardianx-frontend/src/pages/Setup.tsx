import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { Button, Input, Loader } from "@/shared/components";
import HudBackground from "@/shared/layout/HudBackground";
import { useAuth } from "@/hooks/useAuth";
import { setupAdmin } from "@/services/auth";

export default function Setup() {
  const { authenticated, loading, initialized } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loadingForm, setLoadingForm] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-canvas">
        <Loader />
      </div>
    );
  }

  if (authenticated || initialized) {
    return <Navigate to="/login" replace />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setLoadingForm(true);
      await setupAdmin({ username, password });
      setDone(true);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? "Unable to initialize GuardianX.";
      setError(detail);
    } finally {
      setLoadingForm(false);
    }
  }

  if (done) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4">
        <HudBackground />
        <div className="panel relative z-10 w-full max-w-md p-10 text-center shadow-raised">
          <p className="eyebrow mb-2 text-center">Secure Access Gateway</p>
          <h1 className="font-display text-2xl font-bold tracking-[0.18em] text-emerald-400 neon-text">
            GuardianX Initialized
          </h1>
          <p className="mt-4 text-slate-400">
            Your local GuardianX instance is ready. Sign in with your
            administrator credentials to reach the dashboard.
          </p>
          <Link to="/login" className="mt-6 block w-full">
            <Button className="w-full">Continue to Login</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4">
      <HudBackground />
      <div className="panel relative z-10 w-full max-w-md p-10 shadow-raised">
        <p className="eyebrow mb-2 text-center">Secure Access Gateway</p>
        <h1 className="font-display text-center text-3xl font-bold tracking-[0.18em] neon-text glow-text">
          GuardianX
        </h1>
        <p className="mt-3 mb-8 text-center text-slate-400">
          Welcome to your local GuardianX installation.
        </p>
        <p className="-mt-5 mb-8 text-center text-sm text-slate-500">
          Create the administrator account to secure this instance.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="setup-username" className="mb-2 block text-sm font-semibold text-slate-300">
              Username
            </label>
            <Input
              id="setup-username"
              placeholder="Choose an administrator username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              minLength={3}
              maxLength={50}
              required
            />
          </div>

          <div>
            <label htmlFor="setup-password" className="mb-2 block text-sm font-semibold text-slate-300">
              Password
            </label>
            <Input
              id="setup-password"
              type="password"
              placeholder="At least 12 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              minLength={12}
              required
            />
          </div>

          <div>
            <label htmlFor="setup-confirm" className="mb-2 block text-sm font-semibold text-slate-300">
              Confirm Password
            </label>
            <Input
              id="setup-confirm"
              type="password"
              placeholder="Repeat your password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              minLength={12}
              required
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-red-400">
              {error}
            </p>
          )}

          <Button type="submit" disabled={loadingForm} className="w-full">
            {loadingForm ? "Initializing..." : "Initialize GuardianX"}
          </Button>
        </form>
      </div>
    </div>
  );
}
