"use client";

import { useEffect, useState } from "react";
import { listContracts } from "@/lib/api/contracts";
import type { ContractSummary } from "@/lib/types";
import { ContractList } from "@/components/contracts/ContractList";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function ContractsPageClient() {
  const [items, setItems] = useState<ContractSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    void (async () => {
      setLoading(true);
      try {
        const rows = await listContracts();
        setItems(rows);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unable to load contracts");
      } finally {
        setLoading(false);
      }
    })();
  };

  useEffect(() => {
    load();
  }, []);

  if (error != null) {
    return (
      <ErrorState title="Contracts unavailable" message={error} onRetry={load} />
    );
  }

  if (loading || items == null) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Repository"
          description="Every ingested agreement with status-aware triage."
          actions={
            <Button asChild>
              <Link href="/contracts/upload">Upload contract</Link>
            </Button>
          }
        />
        <LoadingState lines={8} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Repository"
        description="Filter by lifecycle state and jump directly into structured reviews."
        actions={
          <Button asChild>
            <Link href="/contracts/upload">Upload contract</Link>
          </Button>
        }
      />
      <ContractList items={items} />
    </div>
  );
}
