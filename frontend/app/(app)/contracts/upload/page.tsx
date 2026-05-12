"use client";

import * as React from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { UploadDropzone } from "@/components/contracts/UploadDropzone";
import type { ContractSummary } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { formatDateTime } from "@/lib/utils";

export default function UploadContractPage() {
  const [recent, setRecent] = React.useState<ContractSummary[]>([]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Secure intake"
        description="Uploads POST to your Legal Agent API. Progress streams attempt to connect over the configured WebSocket endpoint."
      />
      <UploadDropzone
        onUploaded={(summary) => {
          setRecent((prev) => {
            const withoutTemp = prev.filter((c) => !c.id.startsWith("temp_"));
            const merged = [summary, ...withoutTemp];
            const seen = new Set<string>();
            return merged.filter((c) => {
              if (seen.has(c.id)) return false;
              seen.add(c.id);
              return true;
            });
          });
        }}
      />
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Session uploads</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {recent.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Completed uploads appear here with optimistic updates while the API
              responds.
            </p>
          ) : (
            recent.map((c) => (
              <div
                key={c.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border-0 bg-input/50 px-5 py-4 shadow-inset"
              >
                <div>
                  <p className="text-sm font-semibold">{c.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDateTime(c.updated_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="rounded-2xl capitalize">
                    {c.status.replaceAll("_", " ").toLowerCase()}
                  </Badge>
                  {!c.id.startsWith("temp_") && (
                    <Link
                      href={`/contracts/${c.id}`}
                      className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                    >
                      Open review
                    </Link>
                  )}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
