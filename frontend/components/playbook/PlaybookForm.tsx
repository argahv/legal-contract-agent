"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { ClauseType, PlaybookEntry, RiskLevel } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const clauseTypes: ClauseType[] = [
  "LIMITATION_OF_LIABILITY",
  "INDEMNITY",
  "GOVERNING_LAW",
  "TERMINATION",
  "AUTO_RENEWAL",
  "IP_OWNERSHIP",
  "CONFIDENTIALITY",
];

const riskLevels: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

const schema = z.object({
  clause_type: z.enum([
    "LIMITATION_OF_LIABILITY",
    "INDEMNITY",
    "GOVERNING_LAW",
    "TERMINATION",
    "AUTO_RENEWAL",
    "IP_OWNERSHIP",
    "CONFIDENTIALITY",
  ]),
  title: z.string().min(2, "Title is required"),
  guidance: z.string().min(4, "Guidance is required"),
  fallback_language: z.string().optional(),
  risk_floor: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
});

export type PlaybookFormValues = z.infer<typeof schema>;

export function PlaybookForm({
  initial,
  onSubmit,
  submitLabel,
}: {
  initial?: PlaybookEntry;
  onSubmit: (values: PlaybookFormValues) => Promise<void> | void;
  submitLabel: string;
}) {
  const form = useForm<PlaybookFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      clause_type: initial?.clause_type ?? "CONFIDENTIALITY",
      title: initial?.title ?? "",
      guidance: initial?.guidance ?? "",
      fallback_language: initial?.fallback_language ?? "",
      risk_floor: initial?.risk_floor ?? "MEDIUM",
    },
  });

  return (
    <Form {...form}>
      <form
        className="space-y-4"
        onSubmit={form.handleSubmit(async (v) => {
          await onSubmit(v);
        })}
      >
        <FormField
          control={form.control}
          name="clause_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Clause type</FormLabel>
              <Select onValueChange={field.onChange} value={field.value}>
                <FormControl>
                  <SelectTrigger className="rounded-xl">
                    <SelectValue placeholder="Select clause type" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {clauseTypes.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c.replaceAll("_", " ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title</FormLabel>
              <FormControl>
                <Input {...field} className="rounded-xl" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="guidance"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Guidance</FormLabel>
              <FormControl>
                <Textarea {...field} className="min-h-[120px] rounded-xl" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="fallback_language"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Fallback language (optional)</FormLabel>
              <FormControl>
                <Textarea {...field} className="min-h-[80px] rounded-xl" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="risk_floor"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Risk floor</FormLabel>
              <Select onValueChange={field.onChange} value={field.value}>
                <FormControl>
                  <SelectTrigger className="rounded-xl">
                    <SelectValue placeholder="Select floor" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {riskLevels.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button
          type="submit"
          className="rounded-xl"
          disabled={form.formState.isSubmitting}
        >
          {submitLabel}
        </Button>
      </form>
    </Form>
  );
}
