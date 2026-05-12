import { cn } from "@/lib/utils";

export function Progress({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const v = Number.isFinite(value) ? value : 0;
  return (
    <div
      className={cn(
        "relative h-3 w-full overflow-hidden rounded-full bg-background shadow-inset",
        className,
      )}
      role="progressbar"
      aria-valuenow={Math.round(v)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full rounded-full bg-primary shadow-extruded-small transition-all duration-300 ease-out"
        style={{ width: `${Math.min(100, Math.max(0, v))}%` }}
      />
    </div>
  );
}
