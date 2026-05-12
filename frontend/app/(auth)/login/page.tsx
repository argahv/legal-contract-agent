import { Suspense } from "react";
import { LoginForm } from "./login-form";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

function LoginFallback() {
  return (
    <Card className="border-0 p-8 shadow-extruded">
      <Skeleton className="mb-4 h-8 w-48" />
      <Skeleton className="mb-6 h-4 w-full" />
      <Skeleton className="mb-3 h-10 w-full" />
      <Skeleton className="mb-6 h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </Card>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginForm />
    </Suspense>
  );
}
