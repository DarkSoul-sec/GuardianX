import type { ReactNode } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  Lightbulb,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import Card from "@/shared/components/Card";
import { cn } from "@/shared/utils/cn";

export type RecommendationTone = "critical" | "warning" | "info" | "success";

export interface Recommendation {
  id: string;
  tone: RecommendationTone;
  title: string;
  detail: string;
}

const toneConfig: Record<
  RecommendationTone,
  { icon: typeof Info; iconClass: string; label: string }
> = {
  critical: {
    icon: ShieldAlert,
    iconClass: "text-red-400 bg-red-500/10",
    label: "Critical",
  },
  warning: {
    icon: AlertTriangle,
    iconClass: "text-amber-400 bg-amber-500/10",
    label: "Warning",
  },
  info: {
    icon: Info,
    iconClass: "text-cyan-400 bg-cyan-500/10",
    label: "Advisory",
  },
  success: {
    icon: CheckCircle2,
    iconClass: "text-emerald-400 bg-emerald-500/10",
    label: "Healthy",
  },
};

interface Props {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  recommendations: Recommendation[];
}

export default function RecommendationCard({
  title,
  subtitle,
  icon,
  recommendations,
}: Props) {
  return (
    <Card className="space-y-5">
      <div className="flex items-center gap-2">
        <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
          {icon ?? <Sparkles size={18} />}
        </div>
        <div>
          <h2 className="text-xl font-bold">{title}</h2>
          {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
        </div>
      </div>

      <div className="space-y-3">
        {recommendations.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <Lightbulb size={32} className="text-slate-600" />
            <p className="text-sm text-slate-400">
              No recommendations available yet.
            </p>
          </div>
        ) : (
          recommendations.map((recommendation) => {
            const config = toneConfig[recommendation.tone];
            const Icon = config.icon;

            return (
              <div
                key={recommendation.id}
                className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-950/60 p-4"
              >
                <div className={cn("rounded-lg p-2", config.iconClass)}>
                  <Icon size={16} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-slate-100">
                      {recommendation.title}
                    </p>
                    <span className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                      {config.label}
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-slate-400">
                    {recommendation.detail}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
