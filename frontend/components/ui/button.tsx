import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-2xl text-sm font-semibold",
    "transition-all duration-300 ease-out",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-50",
    "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  ].join(" "),
  {
    variants: {
      variant: {
        default: [
          "bg-primary text-primary-foreground shadow-extruded",
          "hover:-translate-y-px hover:shadow-extruded-hover active:translate-y-px",
          "active:shadow-inset-small",
        ].join(" "),
        secondary: [
          "bg-secondary text-secondary-foreground shadow-extruded",
          "hover:-translate-y-px hover:shadow-extruded-hover active:translate-y-px",
          "active:shadow-inset-small",
        ].join(" "),
        destructive: [
          "bg-destructive text-destructive-foreground shadow-extruded",
          "hover:-translate-y-px hover:shadow-extruded-hover active:translate-y-px",
          "active:shadow-inset-small",
        ].join(" "),
        outline: [
          "border-0 bg-background text-primary shadow-extruded",
          "hover:-translate-y-px hover:shadow-extruded-hover active:translate-y-px",
          "active:shadow-inset-small",
        ].join(" "),
        ghost: [
          "text-foreground shadow-none",
          "hover:shadow-extruded-small hover:-translate-y-px active:translate-y-px active:shadow-inset-small",
        ].join(" "),
        link: "rounded-none text-primary underline-offset-4 shadow-none hover:underline",
      },
      size: {
        default: "h-11 min-h-[44px] px-4 py-2",
        sm: "h-9 min-h-0 rounded-xl px-3 text-xs",
        lg: "h-12 min-h-[48px] rounded-2xl px-8 text-base",
        xl: "h-14 min-h-[48px] rounded-2xl px-10 text-base",
        icon: "h-11 w-11 min-h-[44px] min-w-[44px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
