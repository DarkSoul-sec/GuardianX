import { Navigate, Outlet } from "react-router-dom";

import { Loader } from "@/shared/components";
import { useAuth } from "@/hooks/useAuth";

export default function ProtectedRoute() {
  const { authenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-white">
        <Loader />
      </div>
    );
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
