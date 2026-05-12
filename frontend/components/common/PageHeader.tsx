import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mb-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between md:mb-12",
        className,
      )}
    >
      <div className="space-y-2">
        <h1 className="font-display text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {title}
        </h1>
        {description != null && description.length > 0 && (
          <p className="max-w-2xl text-base leading-[1.65] text-muted-foreground md:text-[1.0625rem]">
            {description}
          </p>
        )}
      </div>
      {actions != null && (
        <div className="flex flex-wrap items-center gap-3">{actions}</div>
      )}
    </div>
  );
}
