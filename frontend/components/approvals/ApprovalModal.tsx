"use client";

import * as React from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { ApprovalRequest } from "@/lib/types";
import { resolveApproval } from "@/lib/api/approvals";

export function ApprovalModal({
  open,
  onOpenChange,
  approval,
  onResolved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  approval: ApprovalRequest;
  onResolved?: () => void;
}) {
  const [comment, setComment] = React.useState("");
  const [pending, startTransition] = React.useTransition();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Resolution</DialogTitle>
          <DialogDescription>
            Record a decision for &ldquo;
            {approval.contract?.filename ?? "this contract"}
            &rdquo;. Comments are stored with the audit trail.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="resolution-comment">Comment</Label>
          <Textarea
            id="resolution-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Context for approvers and downstream reviewers"
            className="rounded-xl"
          />
        </div>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            className="rounded-xl"
            onClick={() => onOpenChange(false)}
            disabled={pending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            className="rounded-xl"
            disabled={pending}
            onClick={() => {
              startTransition(() => {
                void (async () => {
                  try {
                    await resolveApproval(approval.id, {
                      status: "REJECTED",
                      comment: comment.length > 0 ? comment : undefined,
                    });
                    toast.success("Marked rejected");
                    onOpenChange(false);
                    onResolved?.();
                  } catch (e) {
                    toast.error(
                      e instanceof Error ? e.message : "Unable to reject",
                    );
                  }
                })();
              });
            }}
          >
            Reject
          </Button>
          <Button
            type="button"
            className="rounded-xl"
            disabled={pending}
            onClick={() => {
              startTransition(() => {
                void (async () => {
                  try {
                    await resolveApproval(approval.id, {
                      status: "APPROVED",
                      comment: comment.length > 0 ? comment : undefined,
                    });
                    toast.success("Marked approved");
                    onOpenChange(false);
                    onResolved?.();
                  } catch (e) {
                    toast.error(
                      e instanceof Error ? e.message : "Unable to approve",
                    );
                  }
                })();
              });
            }}
          >
            Approve
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
