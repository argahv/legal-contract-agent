"use client";

import { useEffect, useState } from "react";
import { useContractProgress } from "@/lib/ws/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ProcessingProgress({
  contractId,
  token,
  autoClearMs,
  className,
}: {
  contractId: string;
  token?: string | null;
  autoClearMs?: number;
  className?: string;
}) {
  const [enabled, setEnabled] = useState(true);
  const { lastMessage, connected, error, reconnect } = useContractProgress(
    contractId,
    enabled,
    token,
  );

  useEffect(() => {
    if (autoClearMs == null || autoClearMs <= 0) return;
    const t = window.setTimeout(() => {
      setEnabled(false);
    }, autoClearMs);
    return () => window.clearTimeout(t);
  }, [autoClearMs]);

  const pct = lastMessage?.progress_percent ?? 0;

  return (
    <Card className={cn("border-0 shadow-inset bg-input/35", className)}>
      <CardContent className="space-y-3 pt-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="font-display text-sm font-bold tracking-tight">
              Processing queue
            </p>
            <p className="text-xs text-muted-foreground">
              WebSocket: {connected ? "connected" : "disconnected"}
              {error != null ? ` — ${error}` : ""}
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => reconnect()}
          >
            Reconnect
          </Button>
        </div>
        <Progress value={Math.min(100, Math.max(0, pct))} />
        <div className="text-xs text-muted-foreground">
          {lastMessage?.step != null && lastMessage.step.length > 0 ? (
            <span className="font-mono">{lastMessage.step}</span>
          ) : (
            <span>Waiting for server updates…</span>
          )}
          {lastMessage?.message != null && lastMessage.message.length > 0 && (
            <span className="mt-1 block text-sm text-foreground">
              {lastMessage.message}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
