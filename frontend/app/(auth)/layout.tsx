import { NeumorphicBackdrop } from "@/components/marketing/NeumorphicBackdrop";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <NeumorphicBackdrop />
      <main
        id="main-content"
        tabIndex={-1}
        className="relative z-10 flex min-h-screen flex-col outline-none"
      >
        <div className="flex flex-1 items-center justify-center px-4 py-12 md:px-6 md:py-16">
          <div className="w-full max-w-md">{children}</div>
        </div>
      </main>
    </div>
  );
}
