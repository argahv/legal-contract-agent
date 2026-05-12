"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  ClipboardCheck,
  FileText,
  Gavel,
  LayoutDashboard,
  Menu,
  ScrollText,
  Upload,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/lib/store/ui";
import {
  useAuthStore,
  canAccessApprovals,
  canEditPlaybook,
  canViewAuditLog,
} from "@/lib/store/auth";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

type NavItem = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
};

function buildNav(
  role: ReturnType<typeof useAuthStore.getState>["user"],
): NavItem[] {
  const items: NavItem[] = [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/contracts", label: "Contracts", icon: FileText },
    { href: "/contracts/upload", label: "Upload", icon: Upload },
  ];
  if (canAccessApprovals(role?.role)) {
    items.push({
      href: "/approvals",
      label: "Approvals",
      icon: ClipboardCheck,
    });
  }
  if (canEditPlaybook(role?.role)) {
    items.push({ href: "/playbook", label: "Playbook", icon: BookOpen });
  }
  if (canViewAuditLog(role?.role)) {
    items.push({ href: "/audit", label: "Audit log", icon: ScrollText });
  }
  return items;
}

function NavLinks({
  collapsed,
  onNavigate,
}: {
  collapsed?: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const role = useAuthStore((s) => s.user);

  return (
    <nav className="flex flex-col gap-1 px-3 py-4" aria-label="Main">
      {/* Brand mark */}
      <div
        className={cn(
          "mb-4 flex items-center gap-2 px-2",
          collapsed === true && "justify-center px-0",
        )}
      >
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-background text-primary shadow-inset-deep">
          <Gavel className="h-5 w-5" aria-hidden />
        </div>
        {collapsed !== true && (
          <div className="min-w-0">
            <p className="truncate font-display text-sm font-bold tracking-tight">
              Legal Agent
            </p>
            <p className="text-xs text-muted-foreground">Contract intelligence</p>
          </div>
        )}
      </div>

      {buildNav(role).map(({ href, label, icon: Icon }) => {
        const active =
          pathname === href ||
          (href !== "/dashboard" && pathname.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            title={label}
            aria-current={active ? "page" : undefined}
            onClick={() => {
              onNavigate?.();
            }}
            className={cn(
              "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-semibold transition-all duration-300 ease-out",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              collapsed === true && "justify-center px-2",
              active
                ? "bg-primary text-primary-foreground shadow-extruded-small"
                : "text-muted-foreground shadow-none hover:-translate-y-px hover:text-foreground hover:shadow-extruded-small active:translate-y-px active:shadow-inset-small",
            )}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden />
            {collapsed !== true ? (
              label
            ) : (
              <span className="sr-only">{label}</span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}

export function Sidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);

  return (
    /* Flat sidebar: solid muted bg, no blur, clear right edge via bg contrast */
    <aside
      className={cn(
        "hidden bg-background shadow-[6px_0_20px_-12px_rgb(163,177,198,0.55)] md:flex md:flex-col",
        collapsed ? "md:w-[72px]" : "md:w-64",
      )}
      aria-label="Sidebar navigation"
    >
      <div className="flex h-14 items-center justify-between px-2">
        {collapsed !== true && (
          <span className="px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Workspace
          </span>
        )}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="shrink-0"
          onClick={() => {
            toggleSidebar();
          }}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <Menu className="h-4 w-4" />
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <NavLinks collapsed={collapsed} />
      </ScrollArea>
    </aside>
  );
}

export function MobileSidebarTrigger() {
  const [open, setOpen] = React.useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="md:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[min(100%,320px)] border-0 bg-background p-0 shadow-extruded">
        <ScrollArea className="h-full">
          <NavLinks onNavigate={() => setOpen(false)} />
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
