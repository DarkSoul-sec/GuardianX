import { useMemo } from "react";
import { ShieldCheck } from "lucide-react";

import VirusTotalIntelPanel from "@/components/virustotal/VirusTotalIntelPanel";

import { Badge, Card } from "@/shared/components";

import { useVirusTotalLookup } from "@/hooks/useVirusTotal";

import type { AssetDetails } from "@/types/asset";
import type { VirusTotalResourceType } from "@/types/virustotal";

interface Props {
  asset: AssetDetails;
}

export default function AssetThreatIntel({ asset }: Props) {
  const indicator = useMemo(() => {
    if (asset.ip_address) {
      return { type: "ip" as VirusTotalResourceType, value: asset.ip_address };
    }
    if (asset.domain) {
      return {
        type: "domain" as VirusTotalResourceType,
        value: asset.domain,
      };
    }
    return null;
  }, [asset.ip_address, asset.domain]);

  const query = useVirusTotalLookup(
    indicator?.type ?? "domain",
    indicator?.value ?? ""
  );

  if (!indicator) return null;

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-xl font-bold text-white">
          <ShieldCheck size={20} className="text-cyan-400" />
          Threat Intelligence
        </h2>

        {query.data?.found && (
          <Badge color={query.data.detected ? "red" : "green"}>
            {query.data.detected ? "Detected" : "Clean"}
          </Badge>
        )}
      </div>

      <VirusTotalIntelPanel
        query={indicator.value}
        data={query.data}
        loading={query.isLoading}
        error={query.error ?? null}
      />
    </Card>
  );
}
