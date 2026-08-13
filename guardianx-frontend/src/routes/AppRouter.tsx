import { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import DashboardLayout from "@/shared/layout/DashboardLayout";
import ProtectedRoute from "@/components/ProtectedRoute";
import RequireRole from "@/components/RequireRole";
import { Loader } from "@/shared/components";
import type { UserRole } from "@/types/user";

const Login = lazy(() => import("@/pages/Login"));
const Setup = lazy(() => import("@/pages/Setup"));
const ForgotPassword = lazy(() => import("@/pages/ForgotPassword"));
const ResetPassword = lazy(() => import("@/pages/ResetPassword"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Assets = lazy(() => import("@/pages/Assets"));
const AssetDetails = lazy(() => import("@/pages/AssetDetails"));
const Findings = lazy(() => import("@/pages/Findings"));
const Scans = lazy(() => import("@/pages/Scans"));
const Reports = lazy(() => import("@/pages/Reports"));
const Settings = lazy(() => import("@/pages/Settings"));
const Copilot = lazy(() => import("@/pages/AICopilot"));
const VirusTotal = lazy(() => import("@/pages/VirusTotal"));
const Phishing = lazy(() => import("@/pages/Phishing"));
const ThreatIntel = lazy(() => import("@/pages/ThreatIntel"));
const ThreatIntelligence = lazy(() => import("@/pages/ThreatIntelligence"));
const Soc = lazy(() => import("@/pages/Soc"));
const Alerts = lazy(() => import("@/pages/Alerts"));
const Incidents = lazy(() => import("@/pages/Incidents"));
const Activity = lazy(() => import("@/pages/Activity"));

function SuspenseLoader() {
  return (
    <div className="flex items-center justify-center py-32">
      <Loader />
    </div>
  );
}

export default function AppRouter() {
  return (
    <Suspense fallback={<SuspenseLoader />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/setup" element={<Setup />} />
        <Route path="/signup" element={<Navigate to="/login" replace />} />
        <Route path="/verify-email" element={<Navigate to="/login" replace />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/assets" element={<Assets />} />
            <Route path="/assets/:id" element={<AssetDetails />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/scans" element={<Scans />} />
            <Route
              path="/reports"
              element={
                <RequireRole
                  roles={[
                    "ADMIN",
                    "SECURITY_ENGINEER",
                    "ANALYST",
                  ] as UserRole[]}
                >
                  <Reports />
                </RequireRole>
              }
            />
            <Route path="/settings" element={<Settings />} />
            <Route path="/copilot" element={<Copilot />} />
            <Route path="/virustotal" element={<VirusTotal />} />
            <Route path="/phishing" element={<Phishing />} />
            <Route path="/threat-intel" element={<ThreatIntel />} />
            <Route path="/intelligence" element={<ThreatIntelligence />} />
            <Route path="/soc" element={<Soc />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/activity" element={<Activity />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
