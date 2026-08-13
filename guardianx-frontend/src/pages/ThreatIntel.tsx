import { useState } from "react";

import { Crosshair, Flame, LineChart, ShieldAlert, TrendingUp } from "lucide-react";

import CveSearchForm from "@/components/threat-intel/CveSearchForm";
import CveDetailModal from "@/components/threat-intel/CveDetailModal";
import CvesTable from "@/components/threat-intel/CvesTable";
import ExploitLikelihoodChart from "@/components/threat-intel/ExploitLikelihoodChart";
import PresetCveSection from "@/components/threat-intel/PresetCveSection";
import RiskTimelineChart from "@/components/threat-intel/RiskTimelineChart";
import SeverityDistributionChart from "@/components/threat-intel/SeverityDistributionChart";
import SourceStatusBadges from "@/components/threat-intel/SourceStatusBadges";
import ThreatIntelStatCards from "@/components/threat-intel/ThreatIntelStatCards";

import { DashboardGrid, PageHeader } from "@/shared/components";

import {
  useThreatIntelSearch,
  useThreatIntelStats,
  useThreatIntelTrending,
} from "@/hooks/useThreatIntel";
import type { ThreatIntelSearchFilters, TrendingCve } from "@/types/threat-intel";

const DEFAULT_FILTERS: ThreatIntelSearchFilters = {
  q: "",
  severity: "",
  year: "",
  vendor: "",
  exploited: false,
  sort: "published",
};

const STAT_WINDOW_DAYS = 14;

const PRESETS = [
  {
    key: "critical",
    title: "Critical CVEs",
    subtitle: "Severity-rated critical, highest risk first",
    icon: <ShieldAlert size={16} className="text-rose-400" />,
    accent: "red" as const,
    filters: {
      q: "",
      severity: "CRITICAL",
      year: "",
      vendor: "",
      exploited: false,
      sort: "risk" as const,
    },
  },
  {
    key: "exploited",
    title: "Known Exploited Vulnerabilities",
    subtitle: "CISA KEV catalog entries",
    icon: <Flame size={16} className="text-amber-400" />,
    accent: "amber" as const,
    filters: {
      q: "",
      severity: "",
      year: "",
      vendor: "",
      exploited: true,
      sort: "epss" as const,
    },
  },
  {
    key: "highest-epss",
    title: "Highest Exploit Probability",
    subtitle: "Top EPSS scores across recent CVEs",
    icon: <LineChart size={16} className="text-cyan-400" />,
    accent: "cyan" as const,
    filters: {
      q: "",
      severity: "",
      year: "",
      vendor: "",
      exploited: false,
      sort: "epss" as const,
    },
  },
];

export default function ThreatIntel() {
  const [filters, setFilters] = useState<ThreatIntelSearchFilters>(DEFAULT_FILTERS);
  const [searching, setSearching] = useState(false);
  const [selectedCve, setSelectedCve] = useState<string | null>(null);

  const statsQuery = useThreatIntelStats(STAT_WINDOW_DAYS);
  const trendingQuery = useThreatIntelTrending(STAT_WINDOW_DAYS, 10);
  const searchQuery = useThreatIntelSearch(filters, searching);

  const items = searching ? searchQuery.data?.items : trendingQuery.data?.items;
  const loading = searching ? searchQuery.isLoading : trendingQuery.isLoading;

  function handleSearch() {
    if (searchQuery.isFetching) return;
    setSearching(true);
  }

  function handleReset() {
    setFilters(DEFAULT_FILTERS);
    setSearching(false);
  }

  function handleSelect(cve: TrendingCve) {
    setSelectedCve(cve.id);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          title="Threat Intelligence Center"
          subtitle="NVD · CISA KEV · FIRST EPSS · MITRE ATT&CK"
        />
        <SourceStatusBadges
          sources={statsQuery.data?.sources}
          loading={statsQuery.isLoading}
        />
      </div>

      <ThreatIntelStatCards
        stats={statsQuery.data}
        loading={statsQuery.isLoading}
      />

      <DashboardGrid columns={3}>
        <SeverityDistributionChart
          data={statsQuery.data?.severity_distribution}
          loading={statsQuery.isLoading}
        />
        <RiskTimelineChart
          data={statsQuery.data?.risk_timeline}
          loading={statsQuery.isLoading}
        />
        <ExploitLikelihoodChart
          data={statsQuery.data?.epss_distribution}
          loading={statsQuery.isLoading}
        />
      </DashboardGrid>

      <div>
        <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
          <Crosshair size={18} className="text-cyan-400" />
          Intelligence Radar
        </h2>
        <div className="grid gap-4 lg:grid-cols-2">
          {PRESETS.map((preset) => (
            <PresetCveSection
              key={preset.key}
              title={preset.title}
              subtitle={preset.subtitle}
              icon={preset.icon}
              accent={preset.accent}
              filters={preset.filters}
              onSelect={handleSelect}
            />
          ))}
          <PresetCveSection
            title="Recently Published"
            subtitle="Latest NVD disclosures"
            icon={<TrendingUp size={16} className="text-emerald-400" />}
            filters={{
              q: "",
              severity: "",
              year: "",
              vendor: "",
              exploited: false,
              sort: "published",
            }}
            onSelect={handleSelect}
          />
        </div>
      </div>

      <CveSearchForm
        filters={filters}
        searching={searchQuery.isFetching}
        onChange={setFilters}
        onSubmit={handleSearch}
        onReset={handleReset}
      />

      <div>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xl font-bold text-white">
            {searching ? "Search Results" : "Trending CVEs"}
          </h2>
          <span className="text-sm text-slate-400">
            {searching
              ? `${searchQuery.data?.total ?? 0} matches`
              : `Most recently published · last ${STAT_WINDOW_DAYS} days`}
          </span>
        </div>

        <CvesTable
          items={items}
          loading={loading}
          onSelect={handleSelect}
          emptyText={
            searching
              ? "No CVEs match your criteria."
              : "No trending CVEs found."
          }
        />
      </div>

      <CveDetailModal
        cveId={selectedCve}
        onClose={() => setSelectedCve(null)}
      />
    </div>
  );
}
