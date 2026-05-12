"use client";

import * as React from "react";
import { Toaster as Sonner } from "sonner";
import { useTheme } from "next-themes";

export function Toaster() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);
  const theme =
    !mounted ? "light" : resolvedTheme === "dark" ? "dark" : "light";

  return (
    <Sonner
      theme={theme}
      position="top-right"
      richColors
      closeButton
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group rounded-2xl border-0 bg-background text-foreground shadow-extruded",
        },
      }}
    />
  );
}
