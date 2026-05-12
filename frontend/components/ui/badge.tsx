import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  [
    "inline-flex items-center rounded-2xl px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide",
    "transition-all duration-300 ease-out",
    "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow-extruded-small",
        secondary:
          "bg-background text-foreground shadow-extruded-small dark:bg-secondary",
        destructive:
          "bg-destructive text-destructive-foreground shadow-extruded-small",
        outline:
          "border-0 bg-transparent text-foreground shadow-inset-small",
        muted: "bg-muted text-muted-foreground shadow-inset-small",
        accent:
          "bg-accent text-accent-foreground shadow-extruded-small",
        success:
          "bg-success text-success-foreground shadow-extruded-small",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
