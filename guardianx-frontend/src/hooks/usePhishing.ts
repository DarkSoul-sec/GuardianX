import { useMutation } from "@tanstack/react-query";

import PhishingService from "@/services/phishing";

export function usePhishingAnalyze() {
  return useMutation({
    mutationFn: (url: string) => PhishingService.analyze(url),
  });
}
