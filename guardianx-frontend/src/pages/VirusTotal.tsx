import { useState } from "react";

import VirusTotalLookupForm from "@/components/virustotal/VirusTotalLookupForm";
import VirusTotalResults from "@/components/virustotal/VirusTotalResults";

import { PageHeader } from "@/shared/components";

import { useVirusTotalLookup } from "@/hooks/useVirusTotal";

import type { VirusTotalResourceType } from "@/types/virustotal";

interface LookupRequest {
  type: VirusTotalResourceType;
  value: string;
}

export default function VirusTotal() {
  const [type, setType] = useState<VirusTotalResourceType>("url");
  const [query, setQuery] = useState("");
  const [request, setRequest] = useState<LookupRequest | null>(null);

  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useVirusTotalLookup(request?.type ?? "url", request?.value ?? "");

  function handleSubmit() {
    const value = query.trim();
    if (!value) return;

    setRequest({ type, value });
  }

  function handleTypeChange(next: VirusTotalResourceType) {
    setType(next);
    setQuery("");
    setRequest(null);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="VirusTotal Intelligence"
        subtitle="URL, domain, IP and SHA256 file hash reputation analysis"
      />

      <VirusTotalLookupForm
        type={type}
        value={query}
        loading={isFetching}
        onTypeChange={handleTypeChange}
        onValueChange={setQuery}
        onSubmit={handleSubmit}
      />

      <VirusTotalResults
        data={data}
        loading={isLoading}
        error={error}
        hasRequest={request !== null}
        onRetry={() => refetch()}
      />
    </div>
  );
}
