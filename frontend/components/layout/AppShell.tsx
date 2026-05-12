"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

function metaForPath(pathname: string): { title: string; subtitle?: string } {
  if (pathname === "/dashboard") {
    return {
      title: "Operations overview",
      subtitle: "Throughput, risk concentration, and recent intake",
    };
  }
  if (pathname === "/contracts") {
    return {
      title: "Contracts",
      subtitle: "Filter by status and open structured reviews",
    };
  }
  if (pathname === "/contracts/upload") {
    return {
      title: "Ingest agreements",
      subtitle: "Drag-and-drop intake with streaming processing feedback",
    };
  }
  if (pathname.startsWith("/contracts/")) {
    return {
      title: "Contract intelligence",
      subtitle: "Source text with clause-level risk and redlines",
    };
  }
  if (pathname === "/approvals") {
    return {
      title: "General Counsel queue",
      subtitle: "Approve or reject with enforceable rationale",
    };
  }
  if (pathname === "/playbook") {
    return {
      title: "Playbook control",
      subtitle: "Clause guidance aligned to your risk appetite",
    };
  }
  if (pathname === "/audit") {
    return { title: "Audit log", subtitle: "Immutable trail of sensitive actions" };
  }
  return { title: "Workspace" };
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const meta = metaForPath(pathname);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={meta.title} subtitle={meta.subtitle} />
        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full max-w-7xl flex-1 overflow-y-auto px-4 pb-20 pt-8 outline-none md:px-10 md:pb-24 md:pt-10"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
