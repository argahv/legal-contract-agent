"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  createPlaybookEntry,
  listPlaybook,
} from "@/lib/api/playbook";
import type { PlaybookEntry } from "@/lib/types";
import { PlaybookForm, type PlaybookFormValues } from "@/components/playbook/PlaybookForm";
import { PlaybookTable } from "@/components/playbook/PlaybookTable";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import {
  useAuthStore,
  canEditPlaybook,
  useAuthHydrated,
} from "@/lib/store/auth";
import { Separator } from "@/components/ui/separator";

export default function PlaybookPageClient() {
  const hydrated = useAuthHydrated();
  const user = useAuthStore((s) => s.user);
  const [items, setItems] = useState<PlaybookEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(() => {
    if (!canEditPlaybook(user?.role)) {
      setItems([]);
      return;
    }
    void (async () => {
      setLoading(true);
      try {
        const rows = await listPlaybook();
        setItems(rows);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unable to load playbook");
      } finally {
        setLoading(false);
      }
    })();
  }, [user?.role]);

  useEffect(() => {
    if (!hydrated) return;
    load();
  }, [hydrated, load]);

  if (!hydrated) {
    return <LoadingState lines={4} />;
  }

  if (!canEditPlaybook(user?.role)) {
    return (
      <EmptyState
        title="Administrator access required"
        description="Playbook maintenance is limited to super administrators and administrators to preserve policy integrity."
      />
    );
  }

  if (error != null) {
    return (
      <ErrorState title="Playbook unavailable" message={error} onRetry={load} />
    );
  }

  if (loading || items == null) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Policy library"
          description="Clause guidance that reviewers see alongside model output."
        />
        <LoadingState lines={8} />
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <PageHeader
        title="Policy library"
        description="Author playbook entries tied to clause archetypes. Changes propagate to reviewers immediately once saved."
      />
      <section className="grid gap-8 lg:grid-cols-2">
        <div>
          <h2 className="mb-4 font-display text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
            Create entry
          </h2>
          <PlaybookForm
            submitLabel="Create playbook entry"
            onSubmit={async (values: PlaybookFormValues) => {
              try {
                await createPlaybookEntry({
                  clause_type: values.clause_type,
                  title: values.title,
                  guidance: values.guidance,
                  fallback_language:
                    values.fallback_language != null &&
                    values.fallback_language.length > 0
                      ? values.fallback_language
                      : undefined,
                  risk_floor: values.risk_floor,
                });
                toast.success("Playbook entry saved");
                load();
              } catch (e) {
                toast.error(
                  e instanceof Error ? e.message : "Unable to save entry",
                );
              }
            }}
          />
        </div>
        <div className="rounded-[32px] border-0 bg-input/40 p-8 shadow-inset text-sm text-muted-foreground">
          <p className="font-display text-base font-bold tracking-tight text-foreground">
            Authoring guidelines
          </p>
          <Separator className="my-4" />
          <ul className="list-disc space-y-2 pl-4">
            <li>Anchor guidance to clause types your models emit.</li>
            <li>Specify minimum acceptable risk to escalate automatically.</li>
            <li>Fallback language should mirror approved vendor paper where possible.</li>
          </ul>
        </div>
      </section>
      <section>
        <h2 className="mb-4 font-display text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
          Existing entries
        </h2>
        <PlaybookTable items={items} onRefresh={load} />
      </section>
    </div>
  );
}
