import { motion, type Variants } from "framer-motion";
import { Gauge, ScanSearch, Server, ShieldAlert } from "lucide-react";

import DashboardHeader from "@/components/dashboard/DashboardHeader";
import SeverityChart from "@/components/dashboard/SeverityChart";
import RiskChart from "@/components/dashboard/RiskChart";
import AssetGrowthChart from "@/components/dashboard/AssetGrowthChart";
import AssetDistributionChart from "@/components/dashboard/AssetDistributionChart";
import FindingsTrendChart from "@/components/dashboard/FindingsTrendChart";
import AttackSurfaceCard from "@/components/dashboard/AttackSurfaceCard";
import RecentFindingsCard from "@/components/dashboard/RecentFindingsCard";
import RecentScansCard from "@/components/dashboard/RecentScansCard";
import TopVulnerableAssetsCard from "@/components/dashboard/TopVulnerableAssetsCard";
import TopVulnerabilitiesCard from "@/components/dashboard/TopVulnerabilitiesCard";
import ThreatIntelWidget from "@/components/dashboard/ThreatIntelWidget";
import DashboardRecommendations from "@/components/dashboard/DashboardRecommendations";

import {
  DashboardGrid,
  ErrorBoundary,
  SecurityScoreCard,
  StatCard,
  SkeletonCard,
} from "@/shared/components";

import { useDashboard } from "@/hooks/useDashboard";

const container: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.07 },
  },
};

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: [0.4, 0, 0.2, 1] },
  },
};

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="mb-8 h-24 animate-pulse rounded-3xl bg-slate-900" />
      <DashboardGrid columns={4}>
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </DashboardGrid>
      <DashboardGrid>
        <SkeletonCard className="h-80" />
        <SkeletonCard className="h-80" />
        <SkeletonCard className="h-80" />
      </DashboardGrid>
      <DashboardGrid>
        <SkeletonCard className="h-80" />
        <SkeletonCard className="h-80" />
        <SkeletonCard className="h-80" />
      </DashboardGrid>
      <DashboardGrid>
        <SkeletonCard className="h-80" />
        <SkeletonCard className="h-80" />
        <SkeletonCard className="h-80" />
      </DashboardGrid>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading, error } = useDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <div className="rounded-2xl border border-red-900/50 bg-red-950/30 p-10 text-center text-red-400">
        Failed to load dashboard.
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        <DashboardHeader />

        <motion.div variants={fadeUp}>
          <DashboardGrid columns={4}>
            <StatCard
              label="Assets"
              value={data.assets}
              icon={<Server size={20} />}
              accent="cyan"
            />
            <StatCard
              label="Scans Completed"
              value={data.completed_scans}
              icon={<ScanSearch size={20} />}
              accent="blue"
            />
            <StatCard
              label="Findings"
              value={data.total_findings}
              icon={<ShieldAlert size={20} />}
              accent="amber"
            />
            <StatCard
              label="Risk Score"
              value={data.risk_score}
              suffix="/100"
              icon={<Gauge size={20} />}
              accent="rose"
              hint={`${data.critical_findings} critical findings`}
            />
          </DashboardGrid>
        </motion.div>

        <motion.div variants={fadeUp}>
          <DashboardGrid>
            <SecurityScoreCard score={data.risk_score} />
            <RiskChart data={data.risk_trend} currentScore={data.risk_score} />
            <AttackSurfaceCard
              openPorts={data.open_ports}
              totalServices={data.total_services}
              totalFindings={data.total_findings}
              completedScans={data.completed_scans}
            />
          </DashboardGrid>
        </motion.div>

        <motion.div variants={fadeUp}>
          <DashboardGrid>
            <AssetDistributionChart data={data.asset_distribution} />
            <FindingsTrendChart data={data.findings_trend} />
            <AssetGrowthChart data={data.asset_growth} />
          </DashboardGrid>
        </motion.div>

        <motion.div variants={fadeUp}>
          <DashboardGrid>
            <ThreatIntelWidget />
            <TopVulnerabilitiesCard vulnerabilities={data.top_vulnerabilities} />
            <SeverityChart
              critical={data.critical_findings}
              high={data.high_findings}
              medium={data.medium_findings}
              low={data.low_findings}
            />
          </DashboardGrid>
        </motion.div>

        <motion.div variants={fadeUp}>
          <DashboardGrid>
            <RecentScansCard scans={data.recent_scans} />
            <RecentFindingsCard findings={data.recent_findings} />
            <TopVulnerableAssetsCard assets={data.top_vulnerable_assets} />
          </DashboardGrid>
        </motion.div>

        <motion.div variants={fadeUp}>
          <DashboardRecommendations data={data} />
        </motion.div>
      </motion.div>
    </ErrorBoundary>
  );
}
