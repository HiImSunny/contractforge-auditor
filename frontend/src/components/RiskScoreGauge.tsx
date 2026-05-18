import { band, BAND_CLASSES } from "@/lib/banding";
import { cn } from "@/lib/utils";

interface Props {
  score: number;
}

export default function RiskScoreGauge({ score }: Props) {
  const b = band(score);
  const r = 80;
  const cx = 100;
  const cy = 100;

  // Arc from left (180°) to right (0°) — semicircle
  const startX = cx - r;
  const startY = cy;
  const endX = cx + r;
  const endY = cy;

  // Coloured arc endpoint
  const angle = Math.PI - (score / 100) * Math.PI;
  const arcX = cx + r * Math.cos(angle);
  const arcY = cy - r * Math.sin(angle);

  const arcColor =
    b === "green" ? "#22c55e" : b === "amber" ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-2">
      <svg viewBox="0 0 200 110" className="w-48 h-24">
        {/* Background track */}
        <path
          d={`M ${startX} ${startY} A ${r} ${r} 0 0 1 ${endX} ${endY}`}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="16"
          strokeLinecap="round"
        />
        {/* Score arc */}
        {score > 0 && (
          <path
            d={`M ${startX} ${startY} A ${r} ${r} 0 0 1 ${arcX} ${arcY}`}
            fill="none"
            stroke={arcColor}
            strokeWidth="16"
            strokeLinecap="round"
          />
        )}
        {/* Score text */}
        <text
          x={cx}
          y={cy + 5}
          textAnchor="middle"
          fontSize="28"
          fontWeight="bold"
          fill="currentColor"
        >
          {score}
        </text>
        <text x={cx} y={cy + 22} textAnchor="middle" fontSize="11" fill="#6b7280">
          / 100
        </text>
      </svg>
      <span
        className={cn(
          "text-xs font-semibold px-2 py-0.5 rounded border uppercase tracking-wide",
          BAND_CLASSES[b]
        )}
      >
        {b === "green" ? "Low Risk" : b === "amber" ? "Medium Risk" : "High Risk"}
      </span>
    </div>
  );
}
