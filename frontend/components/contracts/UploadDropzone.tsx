"use client";

import { useCallback, useState, useTransition } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { uploadContractFile } from "@/lib/api/contracts";
import type { ContractSummary } from "@/lib/types";
import { ProcessingProgress } from "@/components/contracts/ProcessingProgress";
import { useAuthStore } from "@/lib/store/auth";

const ACCEPTED: Record<string, string[]> = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    ".docx",
  ],
  "text/plain": [".txt"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/webp": [".webp"],
  "image/tiff": [".tif", ".tiff"],
};

export function UploadDropzone({
  onUploaded,
  className,
}: {
  onUploaded: (summary: ContractSummary) => void;
  className?: string;
}) {
  const [error, setError] = useState<string | null>(null);
  const [activeContractId, setActiveContractId] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const accessToken = useAuthStore((s) => s.accessToken);

  const uploadFile = useCallback(
    (file: File) => {
      setError(null);
      startTransition(() => {
        void (async () => {
          try {
            const optimistic: ContractSummary = {
              id: `temp_${Date.now().toString(36)}`,
              filename: file.name,
              status: "UPLOADING",
              uploaded_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };
            onUploaded(optimistic);
            const summary = await uploadContractFile(file);
            onUploaded(summary);
            setActiveContractId(summary.id);
            toast.success("Upload started", {
              description: "Processing updates stream in real time when available.",
            });
          } catch (e) {
            const message =
              e instanceof Error ? e.message : "Upload failed. Try again.";
            setError(message);
            toast.error("Upload failed", { description: message });
          }
        })();
      });
    },
    [onUploaded],
  );

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop: (accepted) => {
      const file = accepted[0];
      if (file != null) uploadFile(file);
    },
    maxFiles: 1,
    accept: ACCEPTED,
    disabled: isPending,
    noClick: true,
  });

  return (
    <div className={cn("space-y-4", className)}>
      <div
        {...getRootProps()}
        className={cn(
          "flex min-h-[240px] cursor-pointer flex-col items-center justify-center rounded-[32px] border-0 bg-input/55 px-8 py-14 text-center shadow-inset transition-all duration-300 ease-out",
          isDragActive &&
            "bg-primary/8 shadow-inset-deep ring-2 ring-primary/35 ring-offset-2 ring-offset-background",
          isPending && "pointer-events-none opacity-60",
        )}
      >
        <input {...getInputProps()} aria-label="Upload contract file" />
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-card text-primary shadow-extruded-small">
          <UploadCloud className="h-7 w-7" aria-hidden />
        </div>
        <p className="font-display text-base font-semibold tracking-tight text-foreground">
          Drag and drop a contract file
        </p>
        <p className="mt-2 max-w-md text-xs leading-relaxed text-muted-foreground">
          PDF, DOCX, plain text, or images (JPG, PNG) — one file at a time, up
          to your server limit.
        </p>
        <Button
          type="button"
          className="mt-8"
          onClick={(e) => {
            e.stopPropagation();
            open();
          }}
          disabled={isPending}
        >
          Browse files
        </Button>
      </div>

      {error != null && (
        <Alert variant="destructive">
          <AlertTitle>Upload error</AlertTitle>
          <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setError(null);
                open();
              }}
            >
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {activeContractId != null && (
        <ProcessingProgress
          contractId={activeContractId}
          token={accessToken ?? undefined}
          autoClearMs={12_000}
        />
      )}
    </div>
  );
}
