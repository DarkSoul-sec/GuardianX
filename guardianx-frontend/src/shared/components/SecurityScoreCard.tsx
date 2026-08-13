import { cn } from "@/shared/utils/cn";
import { riskColor, riskLevel } from "@/theme";
import RiskGauge from "./RiskGauge";

interface Props {
  score: number;
  className?: string;
}

export default function SecurityScoreCard({ score, className }: Props) {
  return (
    <div
      className={cn(
        "panel panel-hover flex flex-col items-center justify-center p-6",
        className
      )}
    >
      <div className="mb-5 self-start">
        <h2 className="font-display text-xl font-bold tracking-wide text-slate-100">
          Security Score
        </h2>
        <p className="mt-0.5 text-sm text-slate-400">
          Current posture:{" "}
          <span
            className="font-semibold uppercase tracking-wide"
            style={{ color: riskColor(score) }}
          >
            {riskLevel(score)}
          </span>
        </p>
      </div>
      <RiskGauge score={score} />
    </div>
  );
}
