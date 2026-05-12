"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { toast } from "sonner";
import { loginViaNextRoute } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/store/auth";
import { setSessionMarkerCookie } from "@/lib/session-cookie";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8, "Use at least 8 characters"),
});

export function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const setSession = useAuthStore((s) => s.setSession);

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  return (
    <Card className="border-0 shadow-extruded transition-shadow duration-300 ease-out hover:shadow-extruded-hover">
      <CardHeader>
        <CardTitle className="font-display text-3xl font-bold tracking-tight">
          Welcome back
        </CardTitle>
        <CardDescription>
          Sign in with the account provisioned for your organization.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit(async (values) => {
              try {
                const { tokens, user } = await loginViaNextRoute(
                  values.email,
                  values.password,
                );
                setSession(tokens.access_token, tokens.refresh_token, user);
                setSessionMarkerCookie();
                toast.success("Signed in");
                const next = params.get("from");
                router.push(
                  next != null && next.startsWith("/") ? next : "/dashboard",
                );
                router.refresh();
              } catch (e) {
                toast.error(
                  e instanceof Error ? e.message : "Unable to sign in",
                );
              }
            })}
          >
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Work email</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="username"
                      type="email"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      autoComplete="current-password"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              Continue
            </Button>
          </form>
        </Form>
        <p className="mt-6 text-center text-sm text-muted-foreground">
          New to Legal Agent?{" "}
          <Link
            href="/register"
            className="rounded-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Register your workspace
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
