import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { Button, Input, Loader } from "@/shared/components";
import HudBackground from "@/shared/layout/HudBackground";
import { useAuth } from "@/hooks/useAuth";
import { forgotPassword } from "@/services/auth";

export default function ForgotPassword() {
  const { authenticated, loading, initialized, authMode } = useAuth();

  const [email, setEmail] = useState("");
  const [loadingForm, setLoadingForm] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-canvas">
        <Loader />
      </div>
    );
  }

  if (authenticated) {
    return <Navigate to="/" replace />;
  }

  if (!initialized) {
    return <Navigate to="/setup" replace />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    try {
      setLoadingForm(true);
      await forgotPassword(email);
      setSent(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoadingForm(false);
    }
  }

  if (sent) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4">
        <HudBackground />
        <div className="panel relative z-10 w-full max-w-md p-10 text-center shadow-raised">
          <p className="eyebrow mb-2 text-center">Password Reset</p>
          <h1 className="font-display text-2xl font-bold tracking-[0.18em] text-cyan-300 neon-text">
            Check Your Inbox
          </h1>
          <p className="mt-4 text-slate-400">
            If an account exists for{" "}
            <span className="text-slate-200">{email}</span>, a password reset
            link is on its way.
          </p>
          <Link to="/login">
            <Button variant="secondary" className="mt-6 w-full">
              Back to Login
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4">
      <HudBackground />
      <div className="panel relative z-10 w-full max-w-md p-10 shadow-raised">
        {authMode === "cloud" ? (
          <>
            <p className="eyebrow mb-2 text-center">Account Recovery</p>
            <h1 className="font-display text-center text-3xl font-bold tracking-[0.18em] neon-text glow-text">
              Forgot Password
            </h1>
            <p className="mt-3 mb-8 text-center text-slate-400">
              Enter your email and we'll send you a reset link.
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="forgot-email" className="mb-2 block text-sm font-semibold text-slate-300">
                  Email
                </label>
                <Input
                  id="forgot-email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>

              {error && (
                <p role="alert" className="text-sm text-red-400">
                  {error}
                </p>
              )}

              <Button type="submit" disabled={loadingForm} className="w-full">
                {loadingForm ? "Sending..." : "Send Reset Link"}
              </Button>
            </form>
          </>
        ) : (
          <>
            <p className="eyebrow mb-2 text-center">Account Recovery</p>
            <h1 className="font-display text-center text-3xl font-bold tracking-[0.18em] neon-text glow-text">
              Forgot Password
            </h1>
            <p className="mt-3 mb-8 text-center text-slate-400">
              Local Administrator Recovery
            </p>

            <div className="space-y-4 text-sm text-slate-400">
              <p>
                This is a self-hosted installation. Local administrators are
                recovered at the deployment level — there is no self-service
                email reset for the administrator account.
              </p>
              <p>
                On the machine running the backend, use the bundled recovery
                script:
              </p>
              <pre className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs text-cyan-300">
{`cd backend
.venv/bin/python scripts/reset_admin_password.py`}
              </pre>
              <p>
                This requires access to the server and database, resets the
                password securely, and signs out all active sessions.
              </p>
            </div>
          </>
        )}

        <p className="mt-6 text-center text-sm text-slate-400">
          <Link to="/login" className="text-cyan-400 hover:text-cyan-300">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
