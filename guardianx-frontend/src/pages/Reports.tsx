import { Download, FileText, ShieldAlert, Lightbulb } from "lucide-react";

import {
  Button,
  DashboardGrid,
  DataTable,
  EmptyState,
  PageHeader,
  SkeletonCard,
  StatCard,
} from "@/shared/components";
import type { Column } from "@/shared/components";

import { useExecutiveReport } from "@/hooks/useReports";

import { formatDate } from "@/shared/utils/format";
import { exportRowsToCsv } from "@/shared/utils/csv";

import type { AssetReport, FindingReport } from "@/types/report";

export default function Reports() {
  const { data, isLoading, error, refetch } = useExecutiveReport();

  function exportExecutiveSummary() {
    if (!data) return;

    exportRowsToCsv(
      "guardianx-executive-summary.csv",
      [
        { header: "Generated At", value: () => data.generated_at },
        { header: "Assets", value: () => data.summary.assets },
        { header: "Scans", value: () => data.summary.scans },
        { header: "Critical", value: () => data.summary.critical },
        { header: "High", value: () => data.summary.high },
        { header: "Medium", value: () => data.summary.medium },
        { header: "Low", value: () => data.summary.low },
        { header: "Total Findings", value: () => data.summary.total_findings },
        { header: "Risk Score", value: () => data.summary.risk_score },
      ],
      [0]
    );
  }

  function exportTopAssets() {
    if (!data) return;

    exportRowsToCsv(
      "guardianx-top-assets.csv",
      [
        { header: "Asset", value: (row: AssetReport) => row.name },
        { header: "Type", value: (row: AssetReport) => row.asset_type ?? "" },
        { header: "Domain", value: (row: AssetReport) => row.domain ?? "" },
        { header: "IP Address", value: (row: AssetReport) => row.ip_address ?? "" },
        { header: "Risk Score", value: (row: AssetReport) => row.risk_score },
        { header: "Critical", value: (row: AssetReport) => row.critical },
        { header: "High", value: (row: AssetReport) => row.high },
        { header: "Medium", value: (row: AssetReport) => row.medium },
        { header: "Low", value: (row: AssetReport) => row.low },
        { header: "Total Findings", value: (row: AssetReport) => row.total_findings },
      ],
      data.top_assets
    );
  }

  function exportFindings(asset: AssetReport) {
    exportRowsToCsv(
      `guardianx-findings-${asset.name.replace(/\s+/g, "-").toLowerCase()}.csv`,
      [
        { header: "CVE", value: (row: FindingReport) => row.cve ?? "" },
        { header: "Title", value: (row: FindingReport) => row.title },
        { header: "Severity", value: (row: FindingReport) => row.severity },
        { header: "CVSS", value: (row: FindingReport) => row.cvss ?? "" },
        { header: "Status", value: (row: FindingReport) => row.status },
        { header: "Service", value: (row: FindingReport) => row.affected_service ?? "" },
      ],
      asset.findings
    );
  }

  const assetColumns: Column<AssetReport>[] = [
    {
      key: "name",
      title: "Asset",
      render: (row) => (
        <div>
          <p className="font-semibold text-white">{row.name}</p>
          <p className="text-sm text-slate-400">
            {row.ip_address || row.domain || "-"}
          </p>
        </div>
      ),
    },
    { key: "asset_type", title: "Type" },
    {
      key: "risk_score",
      title: "Risk",
      render: (row) => (
        <span className="font-bold text-white">{row.risk_score}/100</span>
      ),
    },
    {
      key: "total_findings",
      title: "Findings",
      render: (row) => (
        <span className="font-semibold">{row.total_findings}</span>
      ),
    },
    {
      key: "findings",
      title: "Severity",
      render: (row) => (
        <span className="flex items-center gap-1">
          <span className="rounded bg-red-600 px-2 py-0.5 text-xs font-bold">{row.critical}</span>
          <span className="rounded bg-orange-500 px-2 py-0.5 text-xs font-bold">{row.high}</span>
          <span className="rounded bg-yellow-500 px-2 py-0.5 text-xs font-bold">{row.medium}</span>
          <span className="rounded bg-green-600 px-2 py-0.5 text-xs font-bold">{row.low}</span>
        </span>
      ),
    },
    {
      key: "id",
      title: "Export",
      render: (row) => (
        <Button
          variant="secondary"
          onClick={(e) => {
            e.stopPropagation();
            exportFindings(row);
          }}
        >
          <Download size={16} className="mr-2 inline" />
          CSV
        </Button>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="mb-8 h-16 animate-pulse rounded-2xl bg-slate-900" />
        <DashboardGrid columns={4}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </DashboardGrid>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Generate and download security reports"
        action={
          <Button onClick={exportExecutiveSummary} disabled={!data}>
            <Download size={18} className="mr-2 inline" />
            Export Summary
          </Button>
        }
      />

      {error || !data ? (
        <EmptyState
          title="Report Unavailable"
          description="No scan data is available to generate a report yet."
          icon={<FileText size={45} />}
          action={<Button onClick={() => refetch()}>Retry</Button>}
        />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="flex items-center gap-2 text-2xl font-bold text-white">
                  <ShieldAlert className="text-cyan-400" size={24} />
                  Executive Summary
                </h2>
                <p className="mt-1 text-sm text-slate-400">
                  Generated {formatDate(data.generated_at)}
                </p>
              </div>
              <Button variant="secondary" onClick={exportTopAssets}>
                <Download size={16} className="mr-2 inline" />
                Export Top Assets
              </Button>
            </div>
          </div>

          <DashboardGrid columns={4}>
            <StatCard label="Assets Covered" value={data.summary.assets} icon={<FileText size={20} />} accent="cyan" />
            <StatCard label="Scans Run" value={data.summary.scans} icon={<ShieldAlert size={20} />} accent="blue" />
            <StatCard label="Total Findings" value={data.summary.total_findings} icon={<ShieldAlert size={20} />} accent="amber" />
            <StatCard label="Risk Score" value={data.summary.risk_score} suffix="/100" icon={<ShieldAlert size={20} />} accent="rose" />
          </DashboardGrid>

          {data.recommendations.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
                <Lightbulb className="text-yellow-400" size={20} />
                Recommendations
              </h2>
              <ul className="space-y-3">
                {data.recommendations.map((recommendation, index) => (
                  <li key={index} className="flex gap-3 text-slate-300">
                    <span className="mt-1 inline-block h-2 w-2 shrink-0 rounded-full bg-cyan-400" />
                    <span>{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h2 className="mb-4 text-2xl font-bold text-white">
              Top Vulnerable Assets
            </h2>
            <DataTable
              columns={assetColumns}
              data={data.top_assets}
              rowKey={(row) => row.id}
              emptyText="No assets with findings to report."
            />
          </div>
        </>
      )}
    </div>
  );
}
