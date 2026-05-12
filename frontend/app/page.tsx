import Link from "next/link";
import {
  ArrowRight,
  Shield,
  FileStack,
  LineChart,
  CheckCircle2,
  Gavel,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { NeumorphicBackdrop } from "@/components/marketing/NeumorphicBackdrop";

export default function HomePage() {
 return (
    <div className="relative min-h-screen bg-background text-foreground">
      <NeumorphicBackdrop />

      <header className="sticky top-0 z-40 border-0 bg-background/88 shadow-extruded-small backdrop-blur-md backdrop-saturate-150">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 md:px-8">
          <Link
            href="/"
            className="flex items-center gap-3 rounded-2xl py-1 pr-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-background text-primary shadow-inset-deep">
              <Gavel className="h-5 w-5" aria-hidden />
            </span>
            <span className="font-display text-base font-bold tracking-tight">
              Legal Agent
            </span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-3">
            <Button asChild variant="ghost" size="default">
              <Link href="/login">Sign in</Link>
            </Button>
            <Button asChild size="default">
              <Link href="/register">Get started</Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="main-content" tabIndex={-1} className="relative z-10 outline-none">
        {/* Hero */}
        <section className="px-6 py-20 md:px-8 md:py-28 lg:py-32">
          <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-2 lg:items-center lg:gap-16">
            <div className="space-y-8">
              <p className="inline-flex items-center rounded-2xl bg-background px-4 py-2 text-xs font-semibold uppercase tracking-wider text-primary shadow-inset">
                Enterprise contract intelligence
              </p>
              <h1 className="font-display text-4xl font-extrabold leading-[1.1] tracking-tight text-foreground md:text-5xl lg:text-6xl xl:text-7xl">
                Structured reviews for agreements that cannot afford ambiguity.
              </h1>
              <p className="max-w-xl text-lg font-medium leading-relaxed text-muted-foreground md:text-xl">
                Centralize ingestion, clause-level risk, General Counsel approvals,
                and playbook governance in one auditable surface — for teams under
                scrutiny, not slide decks.
              </p>
              <div className="flex flex-wrap gap-4">
                <Button asChild size="lg">
                  <Link href="/register">
                    Start reviewing{" "}
                    <ArrowRight className="h-4 w-4" aria-hidden />
                  </Link>
                </Button>
                <Button asChild variant="secondary" size="lg">
                  <Link href="/login">Access workspace</Link>
                </Button>
              </div>
            </div>

            {/* Hero visual — nested clay cards */}
            <div className="relative mx-auto w-full max-w-md lg:mx-0 lg:max-w-none">
              <div className="rounded-[32px] bg-background p-8 shadow-extruded md:p-10">
                <div className="rounded-2xl bg-background p-6 shadow-inset-deep">
                  <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-primary">
                    Live posture
                  </p>
                  <div className="space-y-3 font-mono text-sm text-foreground">
                    <div className="flex items-center justify-between rounded-xl bg-background px-3 py-2 shadow-extruded-small">
                      <span className="text-muted-foreground">Throughput</span>
                      <span className="font-semibold">Stable</span>
                    </div>
                    <div className="flex items-center justify-between rounded-xl bg-background px-3 py-2 shadow-extruded-small">
                      <span className="text-muted-foreground">Risk mapped</span>
                      <span className="font-semibold text-primary">Clause-level</span>
                    </div>
                    <div className="flex items-center justify-between rounded-xl bg-background px-3 py-2 shadow-extruded-small">
                      <span className="text-muted-foreground">Audit trail</span>
                      <span className="font-semibold text-success">Immutable</span>
                    </div>
                  </div>
                </div>
              </div>
              <div
                aria-hidden
                className="absolute -right-4 -bottom-6 hidden h-24 w-24 rounded-full bg-background shadow-extruded-small animate-float lg:block"
              />
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="px-6 py-20 md:px-8 md:py-24">
          <div className="mx-auto max-w-7xl">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-primary">
              What it does
            </p>
            <h2 className="mb-4 max-w-2xl font-display text-3xl font-bold tracking-tight text-foreground md:text-4xl lg:text-5xl">
              Every step in your contract lifecycle — connected.
            </h2>
            <p className="mb-12 max-w-2xl text-base text-muted-foreground md:text-lg">
              One cool-grey surface, depth from light — so hierarchy stays calm
              while the work stays serious.
            </p>
            <div className="grid gap-8 md:gap-10 lg:grid-cols-3">
              {[
                {
                  icon: FileStack,
                  title: "Operational clarity",
                  body: "Clause-level review panels with explicit risk posture instead of static PDF markups. Same interpretation, linked to source language and policy.",
                },
                {
                  icon: Shield,
                  title: "Defensible approvals",
                  body: "GC queues capture rationale and preserve sign-off for diligence. Approvals attach to contracts with a durable audit trail — not inbox threads.",
                },
                {
                  icon: LineChart,
                  title: "Portfolio signals",
                  body: "Dashboards surface throughput, outstanding risk, and trends aligned with commercial timelines — tied to contract states, not stale exports.",
                },
              ].map(({ icon: Icon, title, body }) => (
                <article
                  key={title}
                  className="group rounded-[32px] bg-background p-8 shadow-extruded transition-all duration-300 ease-out md:p-10 hover:-translate-y-1 hover:shadow-extruded-hover"
                >
                  <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-background text-primary shadow-inset-deep transition-transform duration-500 ease-out group-hover:scale-105">
                    <Icon className="h-6 w-6" aria-hidden />
                  </div>
                  <h3 className="mb-3 font-display text-lg font-bold text-foreground">
                    {title}
                  </h3>
                  <p className="text-sm leading-relaxed text-muted-foreground md:text-base">
                    {body}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Trust */}
        <section className="px-6 py-16 md:px-8 md:py-20">
          <div className="mx-auto max-w-7xl">
            <div className="rounded-[32px] bg-background p-8 shadow-extruded md:p-12 lg:p-16">
              <h2 className="mb-10 text-center font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl">
                Built for teams that can&apos;t afford ambiguity
              </h2>
              <ul className="mx-auto grid max-w-3xl gap-5 md:grid-cols-2 md:gap-6">
                {[
                  "Clause-level risk flags mapped to playbook guidance",
                  "Immutable audit log for every decision",
                  "Role-gated approvals with captured rationale",
                  "Structured redlines — not untracked markup",
                ].map((point) => (
                  <li
                    key={point}
                    className="flex items-start gap-4 rounded-2xl bg-background px-4 py-3 shadow-inset"
                  >
                    <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-background text-success shadow-extruded-small">
                      <CheckCircle2 className="h-4 w-4" aria-hidden />
                    </span>
                    <span className="text-sm font-medium leading-snug text-foreground md:text-base">
                      {point}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="px-6 py-20 md:px-8 md:py-28">
          <div className="mx-auto max-w-7xl">
            <div className="relative overflow-hidden rounded-[32px] bg-primary px-8 py-14 text-center shadow-extruded md:px-16 md:py-20">
              <div
                aria-hidden
                className="pointer-events-none absolute -right-16 top-1/2 h-48 w-48 -translate-y-1/2 rounded-full bg-primary-foreground/10 blur-3xl"
              />
              <div className="relative">
                <h2 className="mb-4 font-display text-3xl font-bold tracking-tight text-primary-foreground md:text-4xl">
                  Ready to bring structure to your agreements?
                </h2>
                <p className="mb-10 text-base font-medium text-primary-foreground/85 md:text-lg">
                  One workspace for intake, review, approval, and governance.
                </p>
                <Button
                  asChild
                  size="lg"
                  variant="secondary"
                  className="bg-background text-primary shadow-extruded hover:shadow-extruded-hover"
                >
                  <Link href="/register">
                    Create your workspace{" "}
                    <ArrowRight className="h-4 w-4" aria-hidden />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-0 bg-background py-12 text-center shadow-[inset_0_8px_24px_-12px_rgb(163,177,198,0.35)]">
        <p className="mx-auto max-w-lg px-6 text-xs font-medium text-muted-foreground md:text-sm">
          Built for production contract operations. Backend integration via
          configurable API endpoints.
        </p>
      </footer>
    </div>
  );
}
