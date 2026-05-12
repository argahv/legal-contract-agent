"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getClauses,
  getContract,
  getRedlines,
  getRisks,
  submitContractForReview,
} from "@/lib/api/contracts";
import type { Clause, Contract, ContractStatus, Redline, RiskAssessment } from "@/lib/types";
import { ClauseCard } from "@/components/contracts/ClauseCard";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/common/PageHeader";
import { toast } from "sonner";

function chunkByParagraphs(source: string, softLimit: number): string[] {
  const normalized = source.replace(/\r\n/g, "\n").trim();
  if (normalized.length === 0) return ["No extracted text for this agreement."];
  const paragraphs = normalized.split(/\n\s*\n+/);
  const chunks: string[] = [];
  let buffer = "";
  for (const p of paragraphs) {
    const piece = p.trim();
    if (piece.length === 0) continue;
    const candidate = buffer.length > 0 ? `${buffer}\n\n${piece}` : piece;
    if (candidate.length > softLimit && buffer.length > 0) {
      chunks.push(buffer);
      buffer = piece;
    } else {
      buffer = candidate;
    }
  }
  if (buffer.length > 0) chunks.push(buffer);
  return chunks.length > 0 ? chunks : [normalized];
}

export function ContractDetailClient() {
  const params = useParams();
  const id = typeof params.id === "string" ? params.id : params.id?.[0];
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [risks, setRisks] = useState<RiskAssessment[]>([]);
  const [redlines, setRedlines] = useState<Redline[]>([]);
  const [contractRecord, setContractRecord] = useState<Contract | null>(null);

  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    if (id == null || id.length === 0) return;
    setLoading(true);
    try {
      const [contract, c, r, rl] = await Promise.all([
        getContract(id),
        getClauses(id),
        getRisks(id),
        getRedlines(id),
      ]);
      setContractRecord(contract);
      setClauses(c);
      setRisks(r);
      setRedlines(rl);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load contract");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const riskByClause = useMemo(() => {
    const map = new Map<string, RiskAssessment>();
    for (const r of risks) {
      map.set(r.clause_id, r);
    }
    return map;
  }, [risks]);

  const redlineByClause = useMemo(() => {
    const map = new Map<string, Redline>();
    for (const r of redlines) {
      map.set(r.clause_id, r);
    }
    return map;
  }, [redlines]);

  const bodyChunks = useMemo(() => {
    const fallback = clauses.map((c) => c.body).join("\n\n");
    const base =
      contractRecord?.content != null && contractRecord.content.length > 0
        ? contractRecord.content
        : fallback;
    return chunkByParagraphs(base, 1100);
  }, [clauses, contractRecord]);

  const downloadReport = useCallback(() => {
    if (id == null || contractRecord == null) return;
    const blob = new Blob(
      [
        JSON.stringify(
          {
            exported_at: new Date().toISOString(),
            contract: contractRecord,
            clauses,
            risks,
            redlines,
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const safeName = contractRecord.filename.replace(/[^a-z0-9-_]+/gi, "_");
    a.download = `legal-agent-${safeName}-${id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Report downloaded");
  }, [id, contractRecord, clauses, risks, redlines]);

  const handleSubmitForReview = useCallback(() => {
    if (id == null) return;
    setSubmitting(true);
    void (async () => {
      try {
        await submitContractForReview(id);
        await load();
        toast.success("Submitted for general counsel review");
      } catch (e) {
        toast.error(
          e instanceof Error ? e.message : "Could not submit for review",
        );
      } finally {
        setSubmitting(false);
      }
    })();
  }, [id, load]);

  if (id == null || id.length === 0) {
    return <ErrorState title="Missing identifier" message="No contract id provided." />;
  }

  if (error != null) {
    return (
      <ErrorState
        title="Review unavailable"
        message={error}
        onRetry={() => void load()}
      />
    );
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Loading contract…"
          description="Fetching document, clauses, risks, and redlines from the API."
          actions={
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" className="rounded-xl" asChild>
                <Link href="/contracts">All contracts</Link>
              </Button>
              <Button variant="outline" size="sm" className="rounded-xl" asChild>
                <Link href="/contracts/upload">Upload</Link>
              </Button>
            </div>
          }
        />
        <Skeleton className="h-12 w-72 rounded-[32px]" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-[480px] rounded-[32px]" />
          <Skeleton className="h-[480px] rounded-[32px]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={
          contractRecord?.filename != null && contractRecord.filename.length > 0
            ? contractRecord.filename
            : "Contract"
        }
        description="Bi-pane review pairs source language with clause intelligence, risk posture, and proposed redlines."
        actions={
          <>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" size="sm" className="rounded-xl" asChild>
                <Link href="/contracts">All contracts</Link>
              </Button>
              <Button variant="outline" size="sm" className="rounded-xl" asChild>
                <Link href="/contracts/upload">Upload</Link>
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="rounded-xl"
                onClick={() => void load()}
              >
                Refresh
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="rounded-xl"
                onClick={downloadReport}
              >
                Export report
              </Button>
              <Button
                type="button"
                variant="default"
                size="sm"
                className="rounded-xl"
                disabled={
                  contractRecord?.status !== "REVIEW" || submitting
                }
                onClick={handleSubmitForReview}
              >
                {submitting ? "Submitting…" : "Submit for review"}
              </Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="rounded-2xl px-3 py-1 text-xs font-semibold capitalize">
                {(contractRecord?.status ?? ("DRAFT" as ContractStatus))
                  .replaceAll("_", " ")
                  .toLowerCase()}
              </Badge>
              {contractRecord?.submitted_for_review_at != null &&
                contractRecord.submitted_for_review_at.length > 0 && (
                  <Badge className="rounded-2xl px-3 py-1 text-xs font-semibold">
                    Submitted for GC
                  </Badge>
                )}
            </div>
          </>
        }
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <section aria-label="Original text" className="min-h-[520px]">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="font-display text-sm font-bold uppercase tracking-[0.12em] text-muted-foreground">
              Source text
            </h2>
            <span className="text-xs text-muted-foreground">
              {bodyChunks.length} scrollable segments
            </span>
          </div>
          <ScrollArea className="h-[520px] rounded-[28px] border-0 bg-card/50 p-5 shadow-inset">
            <div className="space-y-6">
              {bodyChunks.map((chunk, index) => (
                <article key={`chunk-${String(index)}`} className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Section {index + 1}
                  </p>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/95">
                    {chunk}
                  </p>
                  {index < bodyChunks.length - 1 && <Separator className="my-4" />}
                </article>
              ))}
            </div>
          </ScrollArea>
        </section>
        <section aria-label="Clause intelligence" className="space-y-4">
          <h2 className="font-display text-sm font-bold uppercase tracking-[0.12em] text-muted-foreground">
            Clause intelligence
          </h2>
          <div className="space-y-4">
            {clauses.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No clauses were returned — confirm parsing completed on the
                backend.
              </p>
            ) : (
              clauses
                .slice()
                .sort((a, b) => a.sequence - b.sequence)
                .map((clause) => (
                  <ClauseCard
                    key={clause.id}
                    contractId={id}
                    clause={clause}
                    risk={riskByClause.get(clause.id)}
                    redline={redlineByClause.get(clause.id)}
                    onRedlinesChanged={() => void load()}
                  />
                ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
