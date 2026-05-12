"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { listContracts } from "@/lib/api/contracts";
import type { ContractSummary, ContractStatus, RiskLevel } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState, CardGridSkeleton } from "@/components/common/LoadingState";
import Link from "next/link";
import { formatDateTime } from "@/lib/utils";
import { PageHeader } from "@/components/common/PageHeader";

function isTerminalStatus(status: ContractStatus): boolean {
  return (
    status === "APPROVED" ||
    status === "REJECTED" ||
    status === "ERROR"
  );
}

export function DashboardClient() {
  const [items, setItems] = useState<ContractSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const rows = await listContracts();
        setItems(rows);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unable to load dashboard");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const kpis = useMemo(() => {
    if (items == null) {
      return {
        active: 0,
        pendingApproval: 0,
        risk: [] as { level: string; count: number }[],
      };
    }
    const active = items.filter(
      (c) => !isTerminalStatus(c.status),
    ).length;
    const pendingApproval = items.filter(
      (c) => c.status === "PENDING_APPROVAL",
    ).length;

    const tally: Record<RiskLevel, number> = {
      LOW: 0,
      MEDIUM: 0,
      HIGH: 0,
      CRITICAL: 0,
    };
    for (const c of items) {
      if (c.risk_summary == null) continue;
      for (const level of Object.keys(tally) as RiskLevel[]) {
        const n = c.risk_summary[level];
        if (typeof n === "number") tally[level] += n;
      }
    }
    const risk = (Object.keys(tally) as RiskLevel[]).map((level) => ({
      level,
      count: tally[level],
    }));

    return { active, pendingApproval, risk };
  }, [items]);

  if (error != null) {
    return (
      <ErrorState
        title="Dashboard unavailable"
        message={error}
        onRetry={() => {
          setError(null);
          void (async () => {
            setLoading(true);
            try {
              const rows = await listContracts();
              setItems(rows);
            } catch (e) {
              setError(
                e instanceof Error ? e.message : "Unable to load dashboard",
              );
            } finally {
              setLoading(false);
            }
          })();
        }}
      />
    );
  }

  if (loading || items == null) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Operations overview"
          description="Live posture across your contract queue — data streams from your Legal Agent API."
        />
        <CardGridSkeleton count={4} />
        <LoadingState lines={6} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Operations overview"
        description="Active intake, approvals, and risk distribution across the portfolio surfaced from your connected Legal Agent backend."
      />
      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active contracts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-display text-4xl font-bold tracking-tight text-foreground">{kpis.active}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Excludes approved, rejected, and errored files.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending approvals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-display text-4xl font-bold tracking-tight text-foreground">
              {kpis.pendingApproval}
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              Awaiting General Counsel sign-off.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Portfolio risk heatmap
            </CardTitle>
          </CardHeader>
          <CardContent className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={kpis.risk}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--foreground) / 0.08)" />
                <XAxis dataKey="level" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    borderRadius: 20,
                    border: "none",
                    boxShadow:
                      "9px 9px 16px rgb(163,177,198,0.45), -9px -9px 16px rgba(255,255,255,0.45)",
                    background: "hsl(var(--card))",
                    color: "hsl(var(--foreground))",
                  }}
                  formatter={(value: number) => [`${value} findings`, "Count"]}
                />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </section>
      <section>
        <Card>
          <CardHeader>
            <CardTitle>Recent uploads</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="text-right">Open</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-muted-foreground">
                      No contracts indexed yet — ingest a file to populate this
                      workspace view.
                    </TableCell>
                  </TableRow>
                ) : (
                  [...items]
                    .sort(
                      (a, b) =>
                        new Date(b.updated_at).getTime() -
                        new Date(a.updated_at).getTime(),
                    )
                    .slice(0, 6)
                    .map((c) => (
                      <TableRow key={c.id}>
                        <TableCell className="font-medium">{c.filename}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="rounded-2xl capitalize">
                            {c.status.replaceAll("_", " ").toLowerCase()}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDateTime(c.updated_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <Link
                            href={`/contracts/${c.id}`}
                            className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                          >
                            Review
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
