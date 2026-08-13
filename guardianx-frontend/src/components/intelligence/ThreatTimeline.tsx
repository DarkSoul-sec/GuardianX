import { Activity, CalendarClock, Eye, UploadCloud } from "lucide-react";

import { DashboardGrid, TimelineCard } from "@/shared/components";
import { formatDate, formatNumber } from "@/shared/utils/format";

import type { IntelligenceReport } from "@/types/intelligence";

interface Props {
  report: IntelligenceReport;
}

export default function ThreatTimeline({ report }: Props) {
  const submissionItems = [
    {
      id: "first-submission",
      title: "First Submission",
      subtitle: report.first_submission
        ? formatDate(report.first_submission)
        : "Not reported",
      icon: <UploadCloud size={16} />,
    },
    {
      id: "last-submission",
      title: "Last Submission",
      subtitle: report.last_submission
        ? formatDate(report.last_submission)
        : "Not reported",
      icon: <UploadCloud size={16} />,
    },
    {
      id: "times-submitted",
      title: "Times Submitted",
      subtitle: `${formatNumber(report.submission_count)} submission${
        report.submission_count === 1 ? "" : "s"
      }`,
      icon: <Activity size={16} />,
    },
  ];

  const analysisItems = [
    {
      id: "first-seen",
      title: "First Seen",
      subtitle: report.first_seen ? formatDate(report.first_seen) : "Not reported",
      icon: <CalendarClock size={16} />,
    },
    {
      id: "last-analysis",
      title: "Last Analysis",
      subtitle: report.last_analysis
        ? formatDate(report.last_analysis)
        : "Not analyzed",
      icon: <Eye size={16} />,
    },
  ];

  return (
    <DashboardGrid columns={2}>
      <TimelineCard
        title="Submission History"
        items={submissionItems}
        emptyMessage="No submission history reported."
      />
      <TimelineCard
        title="Analysis History"
        items={analysisItems}
        emptyMessage="No analysis history reported."
      />
    </DashboardGrid>
  );
}
