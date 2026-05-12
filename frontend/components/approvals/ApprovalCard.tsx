"use client";

import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ApprovalRequest } from "@/lib/types";
import { ApprovalModal } from "@/components/approvals/ApprovalModal";
import * as React from "react";

function statusBadge(status: ApprovalRequest["status"]) {
  if (status === "APPROVED") return <Badge className="rounded-2xl">Approved</Badge>;
  if (status === "REJECTED") return <Badge variant="destructive" className="rounded-2xl">Rejected</Badge>;
  return <Badge variant="secondary" className="rounded-2xl">Pending</Badge>;
}

export function ApprovalCard({
  item,
  onResolved,
}: {
  item: ApprovalRequest;
  onResolved?: () => void;
}) {
  const [open, setOpen] = React.useState(false);

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
          <div className="space-y-1.5">
            <CardTitle className="text-base font-display font-bold tracking-tight">
              {item.contract?.filename ?? "Contract"}
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Requested {formatDateTime(item.created_at)} ·{" "}
              {item.requested_by.full_name}
            </p>
          </div>
          {statusBadge(item.status)}
        </CardHeader>
        <CardContent className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            {item.comment != null && item.comment.length > 0
              ? item.comment
              : "No reviewer notes supplied."}
          </p>
          {item.status === "PENDING" && (
            <Button type="button" onClick={() => setOpen(true)}>
              Review
            </Button>
          )}
        </CardContent>
      </Card>
      <ApprovalModal
        open={open}
        onOpenChange={setOpen}
        approval={item}
        onResolved={onResolved}
      />
    </>
  );
}
