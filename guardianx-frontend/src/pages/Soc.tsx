import { motion, type Variants } from "framer-motion";
import { AlertTriangle, Radio, ShieldCheck, Target } from "lucide-react";
import { Link } from "react-router-dom";

import AttackSurfaceChart from "@/components/soc/AttackSurfaceChart";
import LiveScansCard from "@/components/soc/LiveScansCard";
import ScanHealthChart from "@/components/soc/ScanHealthChart";
import ActivityTimeline from "@/components/soc/ActivityTimeline";

import {
  DashboardGrid,
  ErrorBoundary,
  PageHeader,
  SkeletonCard,
  StatCard,
} from "@/shared/components";

import { useScanHealth, useSocOverview, useSocRealtime } from "@/hooks/useSoc";

const container: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45 } },
};

function SocSkeleton() {
  return (
    <div className="space-y-6">
      <div className="mb-8 h-20 animate-pulse rounded-3xl bg-slate-900" />
      <DashboardGrid columns={4}>
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </DashboardGrid>
      <DashboardGrid>
        <SkeletonCard className="h-72" />
        <SkeletonCard className="h-72" />
        <SkeletonCard className="h-72" />
      </DashboardGrid>
    </div>
  );
}

export default function Soc() {
  useSocRealtime();
  const { data, isLoading } = useSocOverview();
  const health = useScanHealth();

  if (isLoading && !data) {
    return <SocSkeleton />;
  }

  return (
    <ErrorBoundary>
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        <PageHeader
          title="Security Operations"
          subtitle="Realtime operational posture across scans, alerts, incidents and activity"
        />

        <motion.div variants={fadeUp}>
          <DashboardGrid columns={4}>
            <StatCard
              label="Scan Success Rate"
              value={data?.scans.success_rate ?? 0}
              suffix="%"
              icon={<ShieldCheck size={20} />}
              accent="emerald"
              hint={`${data?.scans.completed ?? 0} completed / ${data?.scans.total ?? 0} total`}
            />
            <StatCard
              label="Running Scans"
              value={data?.scans.running ?? 0}
              icon={<Radio size={20} />}
              accent="cyan"
              hint={`${data?.scans.pending ?? 0} pending in queue`}
            />
            <StatCard
              label="Open Alerts"
              value={data?.alerts.open ?? 0}
              icon={<AlertTriangle size={20} />}
              accent="amber"
              hint={`${data?.alerts.critical ?? 0} critical`}
            />
            <StatCard
              label="Open Incidents"
              value={data?.incidents.open ?? 0}
              icon={<Target size={20} />}
              accent="rose"
              hint={`${data?.scans.failed ?? 0} failed scans`}
            />
          </DashboardGrid>
        </motion.div>

        <motion.div variants={fadeUp}>
          <DashboardGrid>
            <AttackSurfaceChart
              data={data?.attack_surface_trend ?? []}
              loading={isLoading}
            />
            <ScanHealthChart data={health.data} loading={health.isLoading} />
            <LiveScansCard scans={data?.live_scans ?? []} loading={isLoading} />
          </DashboardGrid>
        </motion.div>

        <motion.div variants={fadeUp}>
          <DashboardGrid columns={2}>
            <ActivityTimeline
              items={data?.recent_activity ?? []}
              loading={isLoading}
            />
            <div className="panel panel-hover rounded-2xl p-6">
              <h2 className="mb-4 font-display text-xl font-bold tracking-wide text-slate-100">
                Alert Volume
              </h2>
              <div className="space-y-4">
                {[
                  { label: "Open alerts", value: data?.alerts.open ?? 0 },
                  { label: "Critical alerts", value: data?.alerts.critical ?? 0 },
                  { label: "Total incidents", value: data?.incidents.total ?? 0 },
                ].map((row) => (
                  <div
                    key={row.label}
                    className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3"
                  >
                    <span className="text-sm text-slate-400">{row.label}</span>
                    <span className="font-mono text-lg font-bold text-cyan-300">
                      {row.value}
                    </span>
                  </div>
                ))}
              </div>
              <Link
                to="/incidents"
                className="mt-5 inline-block text-sm font-semibold text-cyan-400 transition hover:text-cyan-300"
              >
                View incidents →
              </Link>
            </div>
          </DashboardGrid>
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}