"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Clause, Redline, RiskAssessment } from "@/lib/types";
import { RiskBadge } from "@/components/contracts/RiskBadge";
import { RedlineDiff } from "@/components/contracts/RedlineDiff";
import { updateRedline } from "@/lib/api/contracts";
import { cn } from "@/lib/utils";

function approvalLabel(status: Redline["status"]): string {
  switch (status) {
    case "PENDING":
      return "Pending";
    case "ACCEPTED":
      return "Accepted";
    case "REJECTED":
      return "Rejected";
    default:
      return "Pending";
  }
}

export function ClauseCard({
  contractId,
  clause,
  risk,
  redline,
  onRedlinesChanged,
  className,
}: {
  contractId: string;
  clause: Clause;
  risk?: RiskAssessment;
  redline?: Redline;
  onRedlinesChanged?: () => void;
  className?: string;
}) {
  const typeLabel = useMemo(() => clause.clause_type.replaceAll("_", " "), [
    clause.clause_type,
  ]);

  const [draftProposed, setDraftProposed] = useState(
    redline?.proposed_text ?? "",
  );
  const [rejectNote, setRejectNote] = useState(
    redline?.reviewer_comment ?? "",
  );
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    setDraftProposed(redline?.proposed_text ?? "");
    setRejectNote(redline?.reviewer_comment ?? "");
  }, [redline?.id, redline?.proposed_text, redline?.reviewer_comment]);

  const runPatch = (body: Parameters<typeof updateRedline>[2]) => {
    if (redline == null) return;
    startTransition(() => {
      void (async () => {
        try {
          await updateRedline(contractId, redline.id, body);
          toast.success("Redline updated");
          onRedlinesChanged?.();
        } catch (e) {
          toast.error(
            e instanceof Error ? e.message : "Could not update redline",
          );
        }
      })();
    });
  };

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="space-y-3 pb-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="text-lg font-bold">{clause.title}</CardTitle>
            <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
              {typeLabel}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {risk != null && <RiskBadge level={risk.level} />}
            {redline != null && (
              <Badge variant="secondary" className="rounded-2xl">
                Redline: {approvalLabel(redline.status)}
              </Badge>
            )}
          </div>
        </div>
        {risk != null && (
          <p className="text-sm text-muted-foreground">{risk.rationale}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs defaultValue="clause" className="w-full">
          <TabsList className="grid w-full grid-cols-2 rounded-2xl">
            <TabsTrigger value="clause">Clause text</TabsTrigger>
            <TabsTrigger value="redline" disabled={redline == null}>
              Redline
            </TabsTrigger>
          </TabsList>
          <TabsContent value="clause" className="mt-4">
            <div className="max-h-48 overflow-auto rounded-2xl bg-background p-4 text-sm leading-relaxed shadow-inset">
              {clause.body}
            </div>
          </TabsContent>
          <TabsContent value="redline" className="mt-4">
            {redline != null ? (
              <div className="space-y-4">
                {redline.rationale != null && redline.rationale.length > 0 && (
                  <p className="text-sm text-muted-foreground">
                    {redline.rationale}
                  </p>
                )}
                {redline.reviewer_comment != null &&
                  redline.reviewer_comment.length > 0 && (
                    <p className="rounded-2xl bg-muted/50 p-3 text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">
                        Reviewer note:{" "}
                      </span>
                      {redline.reviewer_comment}
                    </p>
                  )}
                <Separator />
                <div className="space-y-2">
                  <Label htmlFor={`proposed-${redline.id}`}>
                    Proposed replacement (editable)
                  </Label>
                  <Textarea
                    id={`proposed-${redline.id}`}
                    value={draftProposed}
                    onChange={(e) => setDraftProposed(e.target.value)}
                    className="min-h-[120px] rounded-xl font-mono text-sm"
                    disabled={pending}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor={`reject-${redline.id}`}>
                    Note when rejecting (optional)
                  </Label>
                  <Textarea
                    id={`reject-${redline.id}`}
                    value={rejectNote}
                    onChange={(e) => setRejectNote(e.target.value)}
                    placeholder="Why this redline isn’t acceptable…"
                    className="min-h-[72px] rounded-xl text-sm"
                    disabled={pending}
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    size="sm"
                    className="rounded-xl"
                    disabled={pending || draftProposed.trim().length === 0}
                    onClick={() => {
                      runPatch({ proposed_text: draftProposed.trim() });
                    }}
                  >
                    Save text
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="default"
                    className="rounded-xl"
                    disabled={pending || draftProposed.trim().length === 0}
                    onClick={() => {
                      runPatch({
                        proposed_text: draftProposed.trim(),
                        status: "accepted",
                      });
                    }}
                  >
                    Accept
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="destructive"
                    className="rounded-xl"
                    disabled={pending}
                    onClick={() => {
                      runPatch({
                        status: "rejected",
                        reviewer_comment:
                          rejectNote.trim().length > 0
                            ? rejectNote.trim()
                            : null,
                      });
                    }}
                  >
                    Reject
                  </Button>
                </div>
                <Separator />
                <RedlineDiff
                  original={redline.original_text}
                  proposed={draftProposed}
                />
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No redline for this clause.
              </p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
