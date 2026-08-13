import { Activity, Globe, ShieldAlert } from "lucide-react";

import Badge from "./Badge";
import Card from "./Card";

import { exposureLevel } from "@/theme";

const levelColor: Record<
  "low" | "medium" | "high" | "critical",
  "green" | "yellow" | "orange" | "red"
> = {
  low: "green",
  medium: "yellow",
  high: "orange",
  critical: "red",
};

interface Props {
  score: number;
  internetFacing: boolean;
}

export default function ExposureLevelCard({ score, internetFacing }: Props) {
  const level = exposureLevel(score, internetFacing);

  return (
    <Card className="flex flex-col items-center justify-center">
      <h2 className="mb-5 self-start text-xl font-bold">Exposure Level</h2>

      <div className="flex flex-col items-center gap-2">
        <Badge color={levelColor[level]}>{level.toUpperCase()}</Badge>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <ShieldAlert size={14} />
          <span>
            Attack surface:{" "}
            <span className="font-mono text-slate-200">{score}</span>
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          {internetFacing ? <Globe size={14} /> : <Activity size={14} />}
          <span>
            {internetFacing ? "Internet facing" : "Internal network"}
          </span>
        </div>
      </div>
    </Card>
  );
}
