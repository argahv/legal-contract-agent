/**
 * Ambient depth — same-surface clay orbs (extruded + inset) for marketing shells.
 * Lives behind content; `pointer-events-none` and decorative only.
 */
export function NeumorphicBackdrop() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      <div className="absolute -left-24 top-[12%] h-64 w-64 rounded-full bg-background shadow-extruded md:h-80 md:w-80" />
      <div className="absolute -right-12 top-[28%] h-48 w-48 rounded-full bg-background shadow-inset md:h-64 md:w-64" />
      <div className="absolute bottom-[8%] left-[8%] h-40 w-40 rounded-full bg-background shadow-extruded-small animate-float [animation-delay:1.2s] md:h-56 md:w-56" />
      <div className="absolute bottom-[20%] right-[12%] h-56 w-56 rounded-full bg-background shadow-inset md:h-72 md:w-72" />
      <div className="absolute left-1/2 top-1/3 h-32 w-32 -translate-x-1/2 rounded-full bg-primary/15 shadow-extruded-small blur-sm md:h-40 md:w-40" />
    </div>
  );
}
