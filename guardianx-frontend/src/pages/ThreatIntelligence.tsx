import { useState } from "react";
import { Plug, Radar, ShieldQuestion } from "lucide-react";

import ThreatCards from "@/components/intelligence/ThreatCards";
import ThreatHistory from "@/components/intelligence/ThreatHistory";
import ThreatIndicators from "@/components/intelligence/ThreatIndicators";
import ThreatReputation from "@/components/intelligence/ThreatReputation";
import ThreatSearch from "@/components/intelligence/ThreatSearch";
import ThreatSummary from "@/components/intelligence/ThreatSummary";
import ThreatTimeline from "@/components/intelligence/ThreatTimeline";

import {
  Button,
  Card,
  DashboardGrid,
  EmptyState,
  MotionSection,
  PageHeader,
  SkeletonCard,
  TableSkeleton,
} from "@/shared/components";

import {
  useIntelligenceClearHistory,
  useIntelligenceDeleteHistory,
  useIntelligenceHistory,
  useIntelligenceLookup,
  useIntelligenceStatus,
} from "@/hooks/useIntelligence";

const HISTORY_LIMIT = 10;

export default function ThreatIntelligence() {
  const [query, setQuery] = useState("");
  const [historyType, setHistoryType] = useState("");
  const [historyQuery, setHistoryQuery] = useState("");
  const [historyPage, setHistoryPage] = useState(1);

  const lookup = useIntelligenceLookup();
  const status = useIntelligenceStatus();
  const deleteHistory = useIntelligenceDeleteHistory();
  const clearHistory = useIntelligenceClearHistory();

  const history = useIntelligenceHistory({
    iocType: (historyType || undefined) as
      | "ip"
      | "domain"
      | "url"
      | "hash"
      | undefined,
    q: historyQuery || undefined,
    page: historyPage,
    limit: HISTORY_LIMIT,
  });

  const report = lookup.data?.report;

  function handleSubmit(value: string) {
    const trimmed = value.trim();
    if (!trimmed || lookup.isPending) return;
    setQuery(trimmed);
    lookup.mutate(trimmed);
  }

  function handleQueryChange(value: string) {
    setQuery(value);
    if (lookup.isError) {
      lookup.reset();
    }
  }

  function handleSearchAgain(resource: string) {
    setQuery(resource);
    lookup.mutate(resource);
  }

  function handleDelete(id: number) {
    deleteHistory.mutate(id);
  }

  function handleClearAll() {
    clearHistory.mutate();
  }

  const notConfigured = status.data && !status.data.configured;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Threat Intelligence"
        subtitle="Analyze IP addresses, domains, URLs and SHA256 hashes with cached, risk-scored reports"
      />

      {notConfigured && (
        <Card className="flex flex-col items-start justify-between gap-4 border-amber-500/30 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <div className="rounded-xl border border-amber-400/40 bg-amber-500/10 p-3 text-amber-300">
              <Plug size={20} />
            </div>
            <div>
              <p className="font-semibold text-amber-200">
                VirusTotal provider not configured
              </p>
              <p className="text-sm text-slate-400">
                Add your own VirusTotal API key in Settings &gt; Integrations to
                enable threat intelligence lookups.
              </p>
            </div>
          </div>
          <Button asChild variant="secondary">
            <a href="/settings">
              <Plug size={16} className="mr-2 inline" />
              Configure Integration
            </a>
          </Button>
        </Card>
      )}

      <MotionSection>
        <ThreatSearch
          value={query}
          loading={lookup.isPending}
          onChange={handleQueryChange}
          onSubmit={handleSubmit}
        />
      </MotionSection>

      {lookup.isPending ? (
        <MotionSection delay={0.05}>
          <div className="space-y-6">
            <DashboardGrid columns={4}>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </DashboardGrid>
            <TableSkeleton rows={6} columns={5} />
          </div>
        </MotionSection>
      ) : lookup.isError ? (
        <MotionSection delay={0.05}>
          <EmptyState
            title="Analysis Failed"
            description="The provider could not complete this lookup. Check your integration configuration and try again."
            icon={<ShieldQuestion size={45} />}
            action={
              <Button onClick={() => handleSubmit(query)}>Retry</Button>
            }
          />
        </MotionSection>
      ) : report ? (
        <MotionSection delay={0.05}>
          <div className="space-y-6">
            <ThreatSummary report={report} />
            <ThreatCards report={report} />

            <DashboardGrid columns={2}>
              <ThreatReputation report={report} />
              <ThreatTimeline report={report} />
            </DashboardGrid>

            <ThreatIndicators detections={report.vendor_detections} />
          </div>
        </MotionSection>
      ) : (
        <MotionSection delay={0.05}>
          <EmptyState
            title="Search an indicator to begin"
            description="Enter an IP address, domain, URL or SHA256 hash above. GuardianX detects the IOC type, queries VirusTotal (cached for 24 hours), scores the risk and records the search in your history."
            icon={<Radar size={45} />}
          />
        </MotionSection>
      )}

      <MotionSection delay={0.1}>
        <ThreatHistory
          data={history.data}
          loading={history.isLoading}
          iocTypeFilter={historyType}
          query={historyQuery}
          onIocTypeFilterChange={setHistoryType}
          onQueryChange={setHistoryQuery}
          onPageChange={setHistoryPage}
          onSearchAgain={handleSearchAgain}
          onDelete={handleDelete}
          onClearAll={handleClearAll}
        />
      </MotionSection>
    </div>
  );
}
