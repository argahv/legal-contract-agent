import type { RiskLevel } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { cn, riskLevelTone } from "@/lib/utils";

/** Used when level is missing or not in {@link riskLevelTone} (e.g. API drift). */
const FALLBACK_TONE = {
  label: "Unknown",
  className:
    "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
} as const;

function resolveTone(
  level: RiskLevel | string | null | undefined,
): { label: string; className: string } {
  if (level == null || level === "") return FALLBACK_TONE;
  const key = String(level).toUpperCase() as RiskLevel;
  return riskLevelTone[key] ?? FALLBACK_TONE;
}

export function RiskBadge({
  level,
  className,
}: {
  level: RiskLevel | string | null | undefined;
  className?: string;
}) {
  const tone = resolveTone(level);
  return (
    <Badge
      variant="muted"
      className={cn("font-semibold", tone.className, className)}
    >
      {tone.label}
    </Badge>
  );
}
