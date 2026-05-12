"use client";

import * as React from "react";
import { ThemeProvider, useTheme } from "next-themes";
import { useUiStore } from "@/lib/store/ui";
import { Toaster } from "@/components/ui/sonner";

function ThemePreferenceBridge({
  children,
}: {
  children: React.ReactNode;
}) {
  const themePreference = useUiStore((s) => s.theme);
  const { setTheme } = useTheme();

  React.useEffect(() => {
    setTheme(themePreference);
  }, [themePreference, setTheme]);

  return children;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      enableSystem={false}
      disableTransitionOnChange
    >
      <ThemePreferenceBridge>{children}</ThemePreferenceBridge>
      <Toaster />
    </ThemeProvider>
  );
}
