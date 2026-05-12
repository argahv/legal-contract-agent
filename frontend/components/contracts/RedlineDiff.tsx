"use client";

import { diffChars } from "diff";
import { cn } from "@/lib/utils";

export function RedlineDiff({
  original,
  proposed,
  className,
}: {
  original: string;
  proposed: string;
  className?: string;
}) {
  const parts = diffChars(original, proposed);

  return (
    <div
      className={cn(
        "rounded-2xl bg-background p-4 text-sm leading-relaxed shadow-inset",
        className,
      )}
    >
      <pre className="whitespace-pre-wrap font-mono text-[13px]">
        {parts.map((part, index) => {
          if (part.added === true) {
            return (
              <span
                key={`a-${String(index)}`}
                className="rounded-sm bg-success/25 px-0.5 text-emerald-900 dark:bg-success/20 dark:text-emerald-100"
              >
                {part.value}
              </span>
            );
          }
          if (part.removed === true) {
            return (
              <span
                key={`r-${String(index)}`}
                className="rounded-sm bg-destructive/20 px-0.5 text-destructive line-through dark:bg-destructive/25 dark:text-destructive"
              >
                {part.value}
              </span>
            );
          }
          return <span key={`n-${String(index)}`}>{part.value}</span>;
        })}
      </pre>
    </div>
  );
}
