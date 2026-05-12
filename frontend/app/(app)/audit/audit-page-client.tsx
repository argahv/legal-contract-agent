"use client";

import { useCallback, useEffect, useState } from "react";
import { listAuditLogs, type AuditQuery } from "@/lib/api/audit";
import type { AuditLog } from "@/lib/types";
import { AuditTable } from "@/components/audit/AuditTable";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import {
  useAuthStore,
  canViewAuditLog,
  useAuthHydrated,
} from "@/lib/store/auth";

export default function AuditPageClient() {
  const hydrated = useAuthHydrated();
  const user = useAuthStore((s) => s.user);
  const [items, setItems] = useState<AuditLog[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchLogs = useCallback(async (next: AuditQuery) => {
    setLoading(true);
    try {
      const rows = await listAuditLogs(next);
      setItems(rows);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load audit log");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hydrated || !canViewAuditLog(user?.role)) {
      return;
    }
    void fetchLogs({});
  }, [hydrated, user?.role, fetchLogs]);

  if (!hydrated) {
    return <LoadingState lines={4} />;
  }

  if (!canViewAuditLog(user?.role)) {
    return (
      <EmptyState
        title="Restricted view"
        description="The audit journal is available to super administrators, administrators, and general counsel."
      />
    );
  }

  if (error != null) {
    return (
      <ErrorState
        title="Audit trail unavailable"
        message={error}
        onRetry={() => void fetchLogs({})}
      />
    );
  }

  if (loading || items == null) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Immutable journal"
          description="Tamper-evident history for sensitive operations."
        />
        <LoadingState lines={10} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Immutable journal"
        description="Filter by actor, verb, or time range — results read directly from your Legal Agent audit API."
      />
      <AuditTable
        items={items}
        onFilterChange={(next) => {
          void fetchLogs(next);
        }}
      />
    </div>
  );
}
