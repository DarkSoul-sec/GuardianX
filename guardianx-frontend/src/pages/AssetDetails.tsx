import { Server, Sparkles } from "lucide-react";
import { useNavigate, useParams, Link } from "react-router-dom";

import { assetDeepLink } from "@/shared/utils/copilotLinks";

import AiRecommendationCard from "@/components/assets/AiRecommendationCard";
import AssetHeader from "@/components/assets/AssetHeader";
import AssetThreatIntel from "@/components/assets/AssetThreatIntel";
import AttackSurface from "@/components/assets/AttackSurface";
import RecentFindingsTable from "@/components/assets/RecentFindingsTable";
import RecentScansTimeline from "@/components/assets/RecentScansTimeline";
import RiskOverview from "@/components/assets/RiskOverview";

import {
  Button,
  DashboardGrid,
  EmptyState,
  ErrorBoundary,
  MotionSection,
  PageHeader,
  SkeletonCard,
} from "@/shared/components";

import { useAsset } from "@/hooks/useAssets";

export default function AssetDetails() {
  const navigate = useNavigate();
  const { id } = useParams();
  const assetId = Number(id);

  const { data, isLoading, error } = useAsset(assetId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="mb-8 h-12 w-1/2 animate-pulse rounded-2xl bg-slate-900" />
        <SkeletonCard className="h-40" />
        <DashboardGrid columns={4}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </DashboardGrid>
        <DashboardGrid>
          <SkeletonCard className="h-96" />
          <SkeletonCard className="h-96" />
          <SkeletonCard className="h-96" />
        </DashboardGrid>
      </div>
    );
  }

  if (error || !data) {
    return (
      <EmptyState
        title="Asset Not Found"
        description="This asset may have been removed or you do not have access."
        icon={<Server size={40} />}
        action={
          <Button asChild>
            <Link to="/assets">Back to Assets</Link>
          </Button>
        }
      />
    );
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        <PageHeader
          title={data.name}
          subtitle={`${data.asset_type}${data.ip_address ? ` • ${data.ip_address}` : ""}`}
          action={
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                onClick={() =>
                  navigate("/copilot", { state: assetDeepLink(assetId, data.name) })
                }
              >
                <Sparkles size={16} className="mr-2 inline" />
                Ask Copilot
              </Button>
              <Button asChild variant="secondary">
                <Link to="/assets">Back to Assets</Link>
              </Button>
            </div>
          }
        />

        <MotionSection>
          <AssetHeader asset={data} />
        </MotionSection>
        <MotionSection delay={0.08}>
          <RiskOverview asset={data} />
        </MotionSection>

        <MotionSection delay={0.12}>
          <AssetThreatIntel asset={data} />
        </MotionSection>

        <MotionSection delay={0.16}>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <AttackSurface asset={data} />
            </div>
            <div className="space-y-6">
              <AiRecommendationCard asset={data} />
            </div>
          </div>
        </MotionSection>

        <MotionSection delay={0.24}>
          <RecentFindingsTable asset={data} />
        </MotionSection>

        <MotionSection delay={0.32}>
          <RecentScansTimeline asset={data} />
        </MotionSection>
      </div>
    </ErrorBoundary>
  );
}
