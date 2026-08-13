import { useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";

import { Button, Input } from "@/shared/components";
import HudBackground from "@/shared/layout/HudBackground";
import { useAuth } from "@/hooks/useAuth";
import { resetPassword } from "@/services/auth";

export default function ResetPassword() {
  const { authenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  if (authenticated) {
    return <Navigate to="/" replace />;
  }

  if (!token) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4">
        <HudBackground />
        <div className="panel relative z-10 w-full max-w-md p-10 text-center shadow-raised">
          <h1 className="font-display text-2xl font-bold tracking-[0.18em] text-red-400">
            Invalid Link
          </h1>
          <p className="mt-4 text-slate-400">
            This password reset link is missing a token. Please request a new
            one.
          </p>
          <Link to="/forgot-password">
            <Button variant="secondary" className="mt-6 w-full">
              Request a New Link
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setLoading(true);
      await resetPassword(token, password);
      setDone(true);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? "This reset link is invalid or has expired.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4">
        <HudBackground />
        <div className="panel relative z-10 w-full max-w-md p-10 text-center shadow-raised">
          <p className="eyebrow mb-2 text-center">Success</p>
          <h1 className="font-display text-2xl font-bold tracking-[0.18em] text-cyan-300 neon-text">
            Password Updated
          </h1>
          <p className="mt-4 text-slate-400">
            Your password has been reset. You can now sign in with your new
            password.
          </p>
          <Link to="/login">
            <Button className="mt-6 w-full">Go to Login</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4">
      <HudBackground />
      <div className="panel relative z-10 w-full max-w-md p-10 shadow-raised">
        <p className="eyebrow mb-2 text-center">Account Recovery</p>
        <h1 className="font-display text-center text-3xl font-bold tracking-[0.18em] neon-text glow-text">
          Set New Password
        </h1>
        <p className="mt-3 mb-8 text-center text-slate-400">
          Choose a strong password for your account.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="reset-password" className="mb-2 block text-sm font-semibold text-slate-300">
              New Password
            </label>
            <Input
              id="reset-password"
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
            <label htmlFor="reset-confirm" className="mb-2 block text-sm font-semibold text-slate-300">
              Confirm Password
            </label>
            <Input
              id="reset-confirm"
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

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Resetting..." : "Reset Password"}
          </Button>
        </form>
      </div>
    </div>
  );
}