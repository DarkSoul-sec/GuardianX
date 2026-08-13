import { useMemo, useState } from "react";
import { Play } from "lucide-react";

import ScanDrawer from "@/components/scans/ScanDrawer";
import ScanFilterBar from "@/components/scans/ScanFilterBar";
import type { ScanFilters } from "@/components/scans/ScanFilterBar";
import ScanModal from "@/components/scans/ScanModal";
import ScanOperationsStatus from "@/components/scans/ScanOperationsStatus";
import ScanStats from "@/components/scans/ScanStats";
import ScanTable from "@/components/scans/ScanTable";
import ScheduledScans from "@/components/schedules/ScheduledScans";

import {
  Button,
  EmptyState,
  PageHeader,
  Pagination,
} from "@/shared/components";

import {
  useScansRealtime,
  useCancelScan,
  useScanOperations,
} from "@/hooks/useScans";
import { useNow } from "@/hooks/useNow";
import { useToastContext } from "@/hooks/useToastContext";
import { exportRowsToCsv, type CsvColumn } from "@/shared/utils/csv";

import type { Scan } from "@/types/scan";

const PAGE_SIZE = 8;

const EMPTY_FILTERS: ScanFilters = {
  search: "",
  status: "",
  scanner: "",
};

function scanDurationSeconds(scan: Scan): string {
  if (!scan.started_at || !scan.finished_at) return "";
  const start = new Date(scan.started_at).getTime();
  const end = new Date(scan.finished_at).getTime();
  if (!Number.isFinite(start) || !Number.isFinite(end)) return "";
  return String(Math.max(0, Math.round((end - start) / 1000)));
}

const SCAN_CSV_COLUMNS: CsvColumn<Scan & { duration_seconds: string }>[] = [
  { header: "ID", value: (scan) => scan.id },
  { header: "Asset", value: (scan) => scan.asset_name ?? "" },
  { header: "Status", value: (scan) => scan.status },
  { header: "Scanner", value: (scan) => scan.scanner },
  { header: "Started", value: (scan) => scan.started_at ?? "" },
  { header: "Finished", value: (scan) => scan.finished_at ?? "" },
  { header: "Duration (s)", value: (scan) => scan.duration_seconds },
  { header: "Findings", value: (scan) => scan.finding_count },
  { header: "Created", value: (scan) => scan.created_at },
];

export default function Scans() {
  const {
    data = [],
    isLoading,
    error,
    refetch,
  } = useScansRealtime();
  const { data: operations, isLoading: operationsLoading } =
    useScanOperations();
  const hasActiveScans = data.some(
    (scan) => scan.status === "RUNNING" || scan.status === "PENDING"
  );
  const now = useNow(1000, hasActiveScans);
  const cancelScan = useCancelScan();
  const { success, error: toastError } = useToastContext();

  const [showModal, setShowModal] = useState(false);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);
  const [filters, setFilters] = useState<ScanFilters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  const scanners = useMemo(
    () => Array.from(new Set(data.map((scan) => scan.scanner))).sort(),
    [data]
  );

  const filteredScans = useMemo(() => {
    const query = filters.search.trim().toLowerCase();

    return data.filter((scan) => {
      if (filters.status && scan.status !== filters.status) return false;
      if (filters.scanner && scan.scanner !== filters.scanner) return false;
      if (query) {
        const haystack = [
          String(scan.id),
          scan.asset_name ?? "",
          scan.scanner,
          scan.status,
        ]
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      return true;
    });
  }, [data, filters]);

  const pages = Math.max(1, Math.ceil(filteredScans.length / PAGE_SIZE));
  const currentPage = Math.min(page, pages);
  const pagedScans = filteredScans.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  function handleFiltersChange(next: ScanFilters) {
    setFilters(next);
    setPage(1);
  }

  function handleExport() {
    const rows = data.map((scan) => ({
      ...scan,
      duration_seconds: scanDurationSeconds(scan),
    }));

    exportRowsToCsv(
      `scans-${new Date().toISOString().slice(0, 10)}.csv`,
      SCAN_CSV_COLUMNS,
      rows
    );
  }

  function handleStopScan(scan: Scan) {
    cancelScan.mutate(scan.id, {
      onSuccess: () => {
        success(`Scan #${scan.id} stopped.`);
      },
      onError: () => {
        toastError("Failed to stop scan. It may already be finished.");
      },
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scan Operations Center"
        subtitle="Launch, monitor, and analyze vulnerability scans"
        action={
          <Button onClick={() => setShowModal(true)}>
            <Play size={18} className="mr-2 inline" />
            New Scan
          </Button>
        }
      />

      <ScanStats scans={data} loading={isLoading} />

      <ScanOperationsStatus
        data={operations}
        loading={isLoading || operationsLoading}
      />

      <ScheduledScans />

      <ScanFilterBar
        filters={filters}
        onChange={handleFiltersChange}
        scanners={scanners}
        onExport={handleExport}
      />

      {error ? (
        <EmptyState
          title="Failed to Load Scans"
          description="Unable to fetch scans. Please try again later."
          icon={<Play size={40} />}
          action={
            <Button onClick={() => refetch()}>Retry</Button>
          }
        />
      ) : (
        <>
          <ScanTable
            scans={pagedScans}
            loading={isLoading}
            now={now}
            onSelect={setSelectedScan}
            onStop={handleStopScan}
          />

          {!isLoading && data.length === 0 && (
            <EmptyState
              title="Ready to scan"
              description="Start your first vulnerability scan against a monitored asset."
              icon={<Play size={55} />}
              action={
                <Button onClick={() => setShowModal(true)}>
                  <Play size={18} className="mr-2 inline" />
                  Start Scan
                </Button>
              }
            />
          )}

          <Pagination page={currentPage} pages={pages} onChange={setPage} />
        </>
      )}

      <ScanModal open={showModal} onClose={() => setShowModal(false)} />
      <ScanDrawer scan={selectedScan} onClose={() => setSelectedScan(null)} />
    </div>
  );
}
