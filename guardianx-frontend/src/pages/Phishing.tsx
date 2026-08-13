import { useState } from "react";

import PhishingAnalysisForm from "@/components/phishing/PhishingAnalysisForm";
import PhishingAnalysisResults from "@/components/phishing/PhishingAnalysisResults";

import { PageHeader } from "@/shared/components";

import { usePhishingAnalyze } from "@/hooks/usePhishing";

export default function Phishing() {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const mutation = usePhishingAnalyze();

  function handleSubmit() {
    const value = query.trim();
    if (!value || mutation.isPending) return;

    setSubmitted(true);
    mutation.mutate(value);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Phishing Detection"
        subtitle="Multi-layered analysis of a URL for phishing indicators"
      />

      <PhishingAnalysisForm
        value={query}
        loading={mutation.isPending}
        onValueChange={setQuery}
        onSubmit={handleSubmit}
      />

      <PhishingAnalysisResults
        data={mutation.data}
        loading={mutation.isPending}
        error={mutation.error ?? null}
        hasRequest={submitted}
        onRetry={() => mutation.mutate(query)}
      />
    </div>
  );
}
