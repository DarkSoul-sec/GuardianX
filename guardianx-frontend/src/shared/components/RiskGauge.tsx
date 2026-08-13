import { motion } from "framer-motion";

import { riskColor, riskLevel } from "@/theme";

interface Props {
  score: number;
  size?: number;
  label?: string;
}

/**
 * Animated radial risk gauge for 0-100 scores.
 */
export default function RiskGauge({ score, size = 180, label }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - clamped / 100);
  const color = riskColor(clamped);

  return (
    <div className="relative inline-flex flex-col items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1e293b"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: dashOffset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-4xl font-bold text-white"
          style={{ color }}
        >
          {clamped}
        </motion.span>
        <span className="mt-1 text-xs text-slate-400">
          {label ?? riskLevel(clamped).toUpperCase()}
        </span>
      </div>
    </div>
  );
}
