import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { Button, Input, Loader } from "@/shared/components";
import HudBackground from "@/shared/layout/HudBackground";
import { useAuth } from "@/hooks/useAuth";

export default function Login() {
  const { login, authenticated, loading, initialized } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loadingForm, setLoadingForm] = useState(false);
  const [error, setError] = useState("");

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

    try {
      setLoadingForm(true);
      setError("");

      await login({ username, password });
    } catch {
      setError("Invalid username or password.");
    } finally {
      setLoadingForm(false);
    }
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
          Cyber Security Platform
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="login-username" className="mb-2 block text-sm font-semibold text-slate-300">
              Username
            </label>
            <Input
              id="login-username"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>

          <div>
            <label htmlFor="login-password" className="mb-2 block text-sm font-semibold text-slate-300">
              Password
            </label>
            <Input
              id="login-password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-red-400">
              {error}
            </p>
          )}

          <Button type="submit" disabled={loadingForm} className="w-full">
            {loadingForm ? "Signing In..." : "Login"}
          </Button>
        </form>

        <div className="mt-6 flex justify-center text-sm">
          <Link to="/forgot-password" className="text-slate-400 hover:text-cyan-300">
            Forgot password?
          </Link>
        </div>
      </div>
    </div>
  );
}
