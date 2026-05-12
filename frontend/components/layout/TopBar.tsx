"use client";

import * as React from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "next-themes";
import { useUiStore } from "@/lib/store/ui";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MobileSidebarTrigger } from "@/components/layout/Sidebar";
import { UserMenu } from "@/components/layout/UserMenu";

export function TopBar({ title, subtitle }: { title: string; subtitle?: string }) {
  const themePreference = useUiStore((s) => s.theme);
  const setThemePreference = useUiStore((s) => s.setTheme);
  const { setTheme, resolvedTheme } = useTheme();
  const [themeMounted, setThemeMounted] = React.useState(false);
  React.useEffect(() => setThemeMounted(true), []);

  return (
    /* Flat top bar: solid white bg, bottom border as separator — no blur */
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-0 bg-background/90 px-4 shadow-extruded-small backdrop-blur-md backdrop-saturate-150">
      <MobileSidebarTrigger />
      <div className="min-w-0 flex-1">
        <h1 className="font-display truncate text-lg font-bold tracking-tight text-foreground">
          {title}
        </h1>
        {subtitle != null && subtitle.length > 0 && (
          <p className="truncate text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {subtitle}
          </p>
        )}
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Theme"
          >
            {/* Avoid Sun/Moon SSR vs client mismatch: resolvedTheme reads storage only after mount */}
            {!themeMounted ? (
              <Sun className="h-4 w-4 opacity-60" aria-hidden />
            ) : resolvedTheme === "dark" ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuLabel>Appearance</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuRadioGroup
            value={themePreference}
            onValueChange={(v) => {
              if (v === "system") {
                setTheme("system");
                setThemePreference("system");
              } else if (v === "light") {
                setTheme("light");
                setThemePreference("light");
              } else {
                setTheme("dark");
                setThemePreference("dark");
              }
            }}
          >
            <DropdownMenuRadioItem value="light" className="gap-2">
              <Sun className="h-4 w-4" />
              Light
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="dark" className="gap-2">
              <Moon className="h-4 w-4" />
              Dark
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="system" className="gap-2">
              <Monitor className="h-4 w-4" />
              System
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
      <UserMenu />
    </header>
  );
}
