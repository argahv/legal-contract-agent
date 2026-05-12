import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function LoadingState({
  lines = 4,
  className,
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-3", className)} aria-busy="true">
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={`loading-line-${String(i)}`} className="h-10 w-full" />
      ))}
    </div>
  );
}

export function CardGridSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div
      className="grid gap-4 md:grid-cols-3"
      aria-busy="true"
    >
      {Array.from({ length: count }, (_, i) => (
        <div
          key={`card-skel-${String(i)}`}
          className="rounded-[32px] border-0 bg-card p-6 shadow-extruded"
        >
          <Skeleton className="mb-2 h-4 w-24" />
          <Skeleton className="h-8 w-16" />
        </div>
      ))}
    </div>
  );
}
