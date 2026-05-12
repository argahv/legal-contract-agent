import type { ReactNode } from "react";
import { FileQuestion } from "lucide-react";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  icon,
  className,
  children,
}: {
  title: string;
  description?: string;
  icon?: ReactNode;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-[32px] border-0 bg-input/45 px-8 py-16 text-center shadow-inset",
        className,
      )}
    >
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-card text-muted-foreground shadow-extruded-small">
        {icon ?? <FileQuestion className="h-7 w-7" aria-hidden />}
      </div>
      <h2 className="font-display text-lg font-bold tracking-tight text-foreground">
        {title}
      </h2>
      {description != null && description.length > 0 && (
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          {description}
        </p>
      )}
      {children != null && <div className="mt-6">{children}</div>}
    </div>
  );
}
