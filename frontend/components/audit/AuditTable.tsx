"use client";

import { useMemo, useState, useTransition } from "react";
import type { AuditLog } from "@/lib/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";

export function AuditTable({
  items,
  onFilterChange,
}: {
  items: AuditLog[];
  onFilterChange: (q: {
    action?: string;
    userId?: string;
    from?: string;
    to?: string;
  }) => void;
}) {
  const [action, setAction] = useState("");
  const [userId, setUserId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [, startTransition] = useTransition();

  const rows = useMemo(() => items, [items]);

  return (
    <div className="space-y-4">
      <div className="grid flex-1 gap-3 md:grid-cols-4">
        <Input
          placeholder="Filter by action"
          value={action}
          onChange={(e) => setAction(e.target.value)}
          aria-label="Filter by action"
        />
        <Input
          placeholder="Actor ID (UUID)"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          aria-label="Filter by actor id"
        />
        <Input
          type="datetime-local"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
          aria-label="From timestamp"
        />
        <Input
          type="datetime-local"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          aria-label="To timestamp"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={() => {
            startTransition(() => {
              onFilterChange({
                action: action.length > 0 ? action : undefined,
                userId: userId.length > 0 ? userId : undefined,
                from:
                  from.length > 0 && !Number.isNaN(new Date(from).getTime())
                    ? new Date(from).toISOString()
                    : undefined,
                to:
                  to.length > 0 && !Number.isNaN(new Date(to).getTime())
                    ? new Date(to).toISOString()
                    : undefined,
              });
            });
          }}
        >
          Apply filters
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            setAction("");
            setUserId("");
            setFrom("");
            setTo("");
            onFilterChange({});
          }}
        >
          Clear
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Timestamp</TableHead>
            <TableHead>Actor</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Resource</TableHead>
            <TableHead>Details</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((log) => (
            <TableRow key={log.id}>
              <TableCell className="whitespace-nowrap text-muted-foreground">
                {formatDateTime(log.timestamp)}
              </TableCell>
              <TableCell className="font-mono text-xs">
                {log.user?.id != null ? log.user.id : "—"}
              </TableCell>
              <TableCell>{log.action}</TableCell>
              <TableCell className="text-muted-foreground">
                {log.resource_type}
                {log.resource_id != null && log.resource_id.length > 0
                  ? ` · ${log.resource_id}`
                  : ""}
              </TableCell>
              <TableCell className="max-w-xs truncate text-xs text-muted-foreground">
                {log.metadata != null ? JSON.stringify(log.metadata) : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
