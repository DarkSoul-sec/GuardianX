import { useState } from "react";
import {
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
} from "lucide-react";

import { Badge, Skeleton } from "@/shared/components";

import { formatDate } from "@/shared/utils/format";

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

const PREVIEW_LIMIT = 5;

interface Props {
  query?: string;
  data?: VirusTotalLookupResponse | null;
  loading?: boolean;
  error?: Error | null;
}

export default function VirusTotalIntelPanel({
  query,
  data,
  loading = false,
  error = null,
}: Props) {
  const [showAll, setShowAll] = useState(false);

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        <div className="flex items-center gap-2 font-semibold">
          <ShieldQuestion size={16} />
          VirusTotal lookup failed
        </div>
        <p className="mt-1 text-rose-300/80">
          Make sure your VirusTotal API key is configured and valid in
          Settings &rarr; Integrations, then try again.
        </p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  if (!data.found) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-400">
        No VirusTotal analysis exists for{" "}
        <span className="font-mono text-slate-300">{query ?? data.resource}</span>
        .
      </div>
    );
  }

  const vendors = showAll
    ? data.vendor_detections
    : data.vendor_detections.slice(0, PREVIEW_LIMIT);

  return (
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-950 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`rounded-xl border p-2.5 ${
              data.detected
                ? "border-rose-400/40 bg-rose-500/10 text-rose-300"
                : "border-emerald-400/40 bg-emerald-500/10 text-emerald-300"
            }`}
          >
            {data.detected ? (
              <ShieldAlert size={20} />
            ) : (
              <ShieldCheck size={20} />
            )}
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              VirusTotal
            </p>
            <p className="break-all font-mono text-sm font-semibold text-white">
              {query ?? data.resource}
            </p>
          </div>
        </div>

        <a
          href={data.permalink}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:underline"
        >
          <ExternalLink size={13} />
          View report
        </a>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Detection" value={data.detection_ratio} />
        <Stat label="Malicious" value={String(data.malicious)} />
        <Stat label="Reputation" value={String(data.reputation)} />
        <Stat label="Community" value={String(data.community_score)} />
      </div>

      {(data.threat_category || data.last_analysis_date) && (
        <div className="flex flex-wrap items-center gap-2">
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
      )}

      {data.vendor_detections.length > 0 && (
        <div className="space-y-2">
          {vendors.map((vendor) => (
            <VendorRow key={vendor.engine} vendor={vendor} />
          ))}

          {data.vendor_detections.length > PREVIEW_LIMIT && (
            <button
              type="button"
              onClick={() => setShowAll((current) => !current)}
              className="text-xs font-semibold text-cyan-400 hover:underline"
            >
              {showAll
                ? "Show less"
                : `Show all ${data.vendor_detections.length} vendors`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-0.5 font-mono text-sm font-bold text-white">{value}</p>
    </div>
  );
}

function VendorRow({ vendor }: { vendor: VirusTotalVendorDetection }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="truncate text-slate-300">{vendor.engine}</span>
      <Badge color={verdictColor(vendor.category)}>{vendor.category}</Badge>
    </div>
  );
}
