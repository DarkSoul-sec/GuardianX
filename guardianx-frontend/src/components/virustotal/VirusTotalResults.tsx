import {
  ExternalLink,
  FileSearch,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
} from "lucide-react";

import {
  Badge,
  Button,
  Card,
  DashboardGrid,
  DataTable,
  EmptyState,
  SkeletonCard,
  StatCard,
  TableSkeleton,
} from "@/shared/components";
import type { Column } from "@/shared/components";

import { formatDate, toTitleCase } from "@/shared/utils/format";

import type {
  VirusTotalLookupResponse,
  VirusTotalVendorDetection,
} from "@/types/virustotal";

type BadgeColor = "red" | "yellow" | "green" | "gray";

function verdictColor(category: string): BadgeColor {
  switch (category) {
    case "malicious":
      return "red";
    case "suspicious":
      return "yellow";
    case "clean":
    case "harmless":
      return "green";
    default:
      return "gray";
  }
}

const columns: Column<VirusTotalVendorDetection>[] = [
  { key: "engine", title: "Engine" },
  {
    key: "category",
    title: "Verdict",
    render: (row) => (
      <Badge color={verdictColor(row.category)}>{row.category}</Badge>
    ),
  },
  {
    key: "result",
    title: "Detection",
    render: (row) => row.result ?? "-",
  },
];

interface Props {
  data?: VirusTotalLookupResponse;
  loading: boolean;
  error: Error | null;
  hasRequest: boolean;
  onRetry: () => void;
}

function SummaryCard({ data }: { data: VirusTotalLookupResponse }) {
  const ThreatIcon = data.detected ? ShieldAlert : ShieldCheck;

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div
            className={`rounded-2xl border p-4 ${
              data.detected
                ? "border-rose-400/40 bg-rose-500/10 text-rose-300"
                : "border-emerald-400/40 bg-emerald-500/10 text-emerald-300"
            }`}
          >
            <ThreatIcon size={26} />
          </div>

          <div>
            <p className="eyebrow">
              {toTitleCase(data.resource_type)} Reputation
            </p>
            <h2 className="mt-1 break-all font-mono text-xl font-bold text-white">
              {data.resource}
            </h2>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              {data.detected ? (
                <Badge color="red">Detected</Badge>
              ) : (
                <Badge color="green">Clean</Badge>
              )}

              {data.threat_category && (
                <Badge color={data.detected ? "orange" : "blue"}>
                  {data.threat_category}
                </Badge>
              )}

              {data.last_analysis_date && (
                <span className="text-xs text-slate-500">
                  Analyzed {formatDate(data.last_analysis_date)}
                </span>
              )}
            </div>
          </div>
        </div>

        <Button asChild variant="secondary">
          <a href={data.permalink} target="_blank" rel="noreferrer">
            <ExternalLink size={16} className="mr-2 inline" />
            View on VirusTotal
          </a>
        </Button>
      </div>
    </Card>
  );
}

export default function VirusTotalResults({
  data,
  loading,
  error,
  hasRequest,
  onRetry,
}: Props) {
  if (loading) {
    return (
      <div className="space-y-6">
        <DashboardGrid columns={4}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </DashboardGrid>
        <TableSkeleton rows={6} columns={3} />
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        title="Lookup Failed"
        description="Unable to reach the VirusTotal API. Please check the integration configuration and try again."
        icon={<ShieldQuestion size={45} />}
        action={<Button onClick={onRetry}>Retry</Button>}
      />
    );
  }

  if (!hasRequest || !data) {
    return (
      <EmptyState
        title="No Lookup Yet"
        description="Enter a URL, domain, IP address or SHA256 hash above to start a VirusTotal reputation check."
        icon={<FileSearch size={45} />}
      />
    );
  }

  if (!data.found) {
    return (
      <EmptyState
        title="No VirusTotal Data"
        description={`No analysis exists for ${data.resource}. It may not have been submitted to VirusTotal yet.`}
        icon={<ShieldQuestion size={45} />}
      />
    );
  }

  return (
    <div className="space-y-6">
      <SummaryCard data={data} />

      <DashboardGrid columns={4}>
        <StatCard
          label="Detection Ratio"
          value={data.detection_ratio}
          hint="Malicious engines / total engines"
          icon={<ShieldAlert size={20} />}
          accent={data.detected ? "rose" : "emerald"}
        />
        <StatCard
          label="Malicious"
          value={data.malicious}
          hint={`${data.suspicious} suspicious engines`}
          icon={<ShieldAlert size={20} />}
          accent={data.malicious > 0 ? "rose" : "cyan"}
        />
        <StatCard
          label="Community Score"
          value={data.community_score}
          hint="VirusTotal reputation"
          icon={<ShieldCheck size={20} />}
          accent={data.community_score < 0 ? "amber" : "emerald"}
        />
        <StatCard
          label="Vendors"
          value={data.total}
          hint={`${data.undetected} undetected · ${data.harmless} harmless`}
          icon={<ShieldCheck size={20} />}
          accent="blue"
        />
      </DashboardGrid>

      <div>
        <h2 className="mb-4 text-xl font-bold text-white">
          Vendor Detections
        </h2>
        <DataTable
          columns={columns}
          data={data.vendor_detections}
          rowKey={(row) => row.engine}
          emptyText="No vendor detections reported."
          ariaLabel="VirusTotal vendor detections"
        />
      </div>
    </div>
  );
}
