"use client";

import Link from "next/link";
import { useMemo, useState, useTransition } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ContractStatus, ContractSummary } from "@/lib/types";
import { formatDateTime, cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const STATUSES: ContractStatus[] = [
  "DRAFT",
  "UPLOADING",
  "PROCESSING",
  "REVIEW",
  "PENDING_APPROVAL",
  "APPROVED",
  "REJECTED",
  "ERROR",
];

function statusVariant(
  s: ContractStatus,
): "default" | "secondary" | "destructive" | "outline" {
  if (s === "APPROVED") return "default";
  if (s === "ERROR" || s === "REJECTED") return "destructive";
  if (s === "PENDING_APPROVAL" || s === "REVIEW") return "secondary";
  return "outline";
}

export function ContractList({ items }: { items: ContractSummary[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ContractStatus | "ALL">("ALL");
  const [, startTransition] = useTransition();

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((c) => {
      const matchesQ =
        q.length === 0 ||
        c.filename.toLowerCase().includes(q) ||
        c.id.toLowerCase().includes(q);
      const matchesS = status === "ALL" || c.status === status;
      return matchesQ && matchesS;
    });
  }, [items, query, status]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => {
              startTransition(() => setQuery(e.target.value));
            }}
            placeholder="Search by filename or identifier"
            className="rounded-2xl pl-10"
            aria-label="Search contracts"
          />
        </div>
        <Select
          value={status}
          onValueChange={(v) => {
            setStatus(v as ContractStatus | "ALL");
          }}
        >
          <SelectTrigger className="w-full sm:w-52">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>
                {s.replaceAll("_", " ")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            setQuery("");
            setStatus("ALL");
          }}
        >
          Reset filters
        </Button>
      </div>

      <Card className="overflow-hidden border-0">
        <CardContent className="overflow-x-auto p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk snapshot</TableHead>
                <TableHead>Updated</TableHead>
                <TableHead className="text-right">Open</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.filename}</TableCell>
                  <TableCell>
                    <Badge
                      variant={statusVariant(c.status)}
                      className="rounded-2xl capitalize"
                    >
                      {c.status.replaceAll("_", " ").toLowerCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {c.risk_summary != null ? (
                      <span className="text-xs">
                        {Object.entries(c.risk_summary)
                          .filter(([, n]) => (n ?? 0) > 0)
                          .map(([k, n]) => `${k}: ${String(n)}`)
                          .join(" · ") || "—"}
                      </span>
                    ) : (
                      "—"
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDateTime(c.updated_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link
                      href={`/contracts/${c.id}`}
                      className={cn(
                        "text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm px-1",
                      )}
                    >
                      View
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
