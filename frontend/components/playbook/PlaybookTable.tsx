"use client";

import * as React from "react";
import { toast } from "sonner";
import { Pencil, Trash2 } from "lucide-react";
import type { PlaybookEntry } from "@/lib/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/contracts/RiskBadge";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { PlaybookForm, type PlaybookFormValues } from "@/components/playbook/PlaybookForm";
import { deletePlaybookEntry, updatePlaybookEntry } from "@/lib/api/playbook";
import { formatShortDate } from "@/lib/utils";

export function PlaybookTable({ items, onRefresh }: { items: PlaybookEntry[]; onRefresh: () => void }) {
  const [editing, setEditing] = React.useState<PlaybookEntry | null>(null);

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Floor</TableHead>
            <TableHead>Updated</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((row) => (
            <TableRow key={row.id}>
              <TableCell className="font-medium">{row.title}</TableCell>
              <TableCell className="text-muted-foreground">
                {row.clause_type.replaceAll("_", " ")}
              </TableCell>
              <TableCell>
                <RiskBadge level={row.risk_floor} className="rounded-2xl" />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatShortDate(row.updated_at)}
              </TableCell>
              <TableCell className="text-right space-x-2">
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  className="rounded-xl"
                  aria-label={`Edit ${row.title}`}
                  onClick={() => setEditing(row)}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  className="rounded-xl text-destructive"
                  aria-label={`Delete ${row.title}`}
                  onClick={() => {
                    void (async () => {
                      try {
                        await deletePlaybookEntry(row.id);
                        toast.success("Playbook entry removed");
                        onRefresh();
                      } catch (e) {
                        toast.error(
                          e instanceof Error ? e.message : "Delete failed",
                        );
                      }
                    })();
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Sheet open={editing != null} onOpenChange={() => setEditing(null)}>
        <SheetContent className="w-full sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Edit playbook entry</SheetTitle>
          </SheetHeader>
          {editing != null && (
            <div className="mt-6">
              <PlaybookForm
                key={editing.id}
                initial={editing}
                submitLabel="Save changes"
                onSubmit={async (values: PlaybookFormValues) => {
                  try {
                    await updatePlaybookEntry(editing.id, values);
                    toast.success("Playbook updated");
                    setEditing(null);
                    onRefresh();
                  } catch (e) {
                    toast.error(
                      e instanceof Error ? e.message : "Unable to update",
                    );
                  }
                }}
              />
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
