"use client";

import { useCallback, useEffect, useState } from "react";
import { listApprovals } from "@/lib/api/approvals";
import type { ApprovalRequest } from "@/lib/types";
import { ApprovalCard } from "@/components/approvals/ApprovalCard";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import {
  useAuthStore,
  canAccessApprovals,
  useAuthHydrated,
} from "@/lib/store/auth";

export default function ApprovalsPageClient() {
  const hydrated = useAuthHydrated();
  const user = useAuthStore((s) => s.user);
  const [items, setItems] = useState<ApprovalRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(() => {
    if (!canAccessApprovals(user?.role)) {
      setItems([]);
      return;
    }
    void (async () => {
      setLoading(true);
      try {
        const rows = await listApprovals();
        setItems(rows);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unable to load approvals");
      } finally {
        setLoading(false);
      }
    })();
  }, [user?.role]);

  useEffect(() => {
    if (!hydrated) return;
    load();
  }, [hydrated, load]);

  if (!hydrated) {
    return <LoadingState lines={4} />;
  }

  if (!canAccessApprovals(user?.role)) {
    return (
      <EmptyState
        title="Restricted view"
        description="Super administrators, administrators, and general counsel may sign off here."
      />
    );
  }

  if (error != null) {
    return (
      <ErrorState title="Queue unavailable" message={error} onRetry={load} />
    );
  }

  if (loading || items == null) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="GC queue"
          description="Structured sign-off with immutable commentary."
        />
        <LoadingState lines={6} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="GC queue"
        description="Approve or push back with rationale — every decision is journaled."
      />
      {items.length === 0 ? (
        <EmptyState
          title="No pending work"
          description="When contracts require executive approval they surface here automatically."
        />
      ) : (
        <div className="grid gap-4">
          {items.map((item) => (
            <ApprovalCard key={item.id} item={item} onResolved={load} />
          ))}
        </div>
      )}
    </div>
  );
}
