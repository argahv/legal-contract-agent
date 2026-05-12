import { Suspense } from "react";
import { DashboardClient } from "./dashboard-client";
import { CardGridSkeleton } from "@/components/common/LoadingState";

export const dynamic = "force-dynamic";

export default function DashboardPage() {
  return (
    <Suspense fallback={<CardGridSkeleton count={4} />}>
      <DashboardClient />
    </Suspense>
  );
}
