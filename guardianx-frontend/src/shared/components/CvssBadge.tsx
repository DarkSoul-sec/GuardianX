import Badge from "./Badge";

interface Props {
  score: number | null;
}

export default function CvssBadge({ score }: Props) {
  if (score === null) {
    return <span className="text-slate-500">-</span>;
  }

  let color: "green" | "yellow" | "orange" | "red" = "green";

  if (score >= 9) color = "red";
  else if (score >= 7) color = "orange";
  else if (score >= 4) color = "yellow";

  return <Badge color={color}>{score.toFixed(1)}</Badge>;
}
