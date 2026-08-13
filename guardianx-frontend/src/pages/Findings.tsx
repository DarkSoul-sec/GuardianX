import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Download, Sparkles } from "lucide-react";

import type { CopilotDeepLink } from "@/types/copilot";

import BulkTriageBar from "@/components/findings/BulkTriageBar";
import FindingFilters from "@/components/findings/FindingFilters";
import FindingsTable from "@/components/findings/FindingsTable";
import FindingDrawer from "@/components/findings/FindingDrawer";
import FindingStats from "@/components/findings/FindingStats";

import {
  Button,
  EmptyState,
  PageHeader,
  Pagination,
  SearchInput,
  TableSkeleton,
} from "@/shared/components";

import { useAssets } from "@/hooks/useAssets";
import {
  useFindings,
  useFindingsRealtime,
  useExportFindings,
} from "@/hooks/useFindings";
import { useToastContext } from "@/hooks/useToastContext";
import type { FindingSeverity, FindingStatus } from "@/types/finding";

export default function Findings() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState<FindingSeverity | "">("");
  const [status, setStatus] = useState<FindingStatus | "">("");
  const [asset, setAsset] = useState("");
  const [assigned, setAssigned] = useState<"" | "me" | "unassigned">("");
  const [search, setSearch] = useState(searchParams.get("q") ?? "");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const { error: toastError } = useToastContext();
  const exportFindings = useExportFindings();

  useFindingsRealtime();

  useEffect(() => {
    const q = searchParams.get("q");
    if (q !== null && q !== search) {
      setSearch(q);
      setPage(1);
    }
  }, [searchParams, search]);

  const { data: assets = [] } = useAssets();
  const { data, isLoading, error, refetch } = useFindings({
    page,
    size: 20,
    severity: severity || undefined,
    status: status || undefined,
    asset: asset || undefined,
    assigned: assigned || undefined,
    search: search || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  function resetPage() {
    setPage(1);
  }

  function handleSeverity(value: string) {
    setSeverity(value as FindingSeverity);
    resetPage();
  }

  function handleStatus(value: string) {
    setStatus(value as FindingStatus);
    resetPage();
  }

  function handleAskCopilot() {
    const deepLink: CopilotDeepLink = {
      intent: "prioritize",
      prompt: "Prioritize vulnerabilities across my estate.",
    };
    navigate("/copilot", { state: deepLink });
  }

  function handleExport() {
    exportFindings.mutate(
      {
        severity: severity || undefined,
        status: status || undefined,
        asset: asset || undefined,
        assigned: assigned || undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      },
      {
        onError: () => {
          toastError("Failed to export findings.");
        },
      }
    );
  }

  function toggleSelect(id: number) {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll(ids: number[]) {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      const allPresent = ids.every((id) => next.has(id));
      ids.forEach((id) => {
        if (allPresent) next.delete(id);
        else next.add(id);
      });
      return next;
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Findings"
        subtitle="Detected vulnerabilities across your assets"
        action={
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={handleAskCopilot}>
              <Sparkles size={16} className="mr-2 inline" />
              Ask Copilot
            </Button>
            <Button
              variant="secondary"
              onClick={handleExport}
              disabled={exportFindings.isPending}
            >
              <Download size={16} className="mr-2 inline" />
              {exportFindings.isPending ? "Exporting..." : "Export CSV"}
            </Button>
          </div>
        }
      />

      <FindingStats loading={isLoading} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="lg:max-w-xs lg:flex-1">
          <SearchInput
            value={search}
            onChange={(value) => {
              setSearch(value);
              resetPage();
            }}
            placeholder="Search by CVE, title, asset..."
          />
        </div>
        <FindingFilters
          severity={severity}
          status={status}
          asset={asset}
          assigned={assigned}
          sortBy={sortBy}
          sortOrder={sortOrder}
          assets={assets.map((item) => item.name)}
          onSeverity={handleSeverity}
          onStatus={handleStatus}
          onAsset={(value) => {
            setAsset(value);
            resetPage();
          }}
          onAssigned={(value) => {
            setAssigned(value);
            resetPage();
          }}
          onSortBy={(value) => {
            setSortBy(value);
            resetPage();
          }}
          onSortOrder={(value) => {
            setSortOrder(value);
            resetPage();
          }}
        />
      </div>

      <BulkTriageBar
        selectedIds={Array.from(selectedIds)}
        onClear={() => setSelectedIds(new Set())}
      />

      {isLoading ? (
        <TableSkeleton rows={6} columns={6} />
      ) : error || !data ? (
        <EmptyState
          title="Failed to Load Findings"
          description="Unable to fetch findings. Please try again later."
          action={<Button onClick={() => refetch()}>Retry</Button>}
        />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No Findings"
          description="No vulnerabilities match your current filters."
        />
      ) : (
        <>
          <FindingsTable
            findings={data.items}
            selectedIds={selectedIds}
            onSelect={setSelectedId}
            onToggleSelect={toggleSelect}
            onToggleAll={toggleAll}
          />
          <Pagination
            page={data.page}
            pages={Math.max(data.pages, 1)}
            onChange={setPage}
          />
        </>
      )}

      <FindingDrawer id={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
