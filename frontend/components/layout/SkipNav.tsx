/**
 * UI/UX Pro Max (ux: skip links) — first focusable control so keyboard users
 * bypass repeated navigation chrome.
 */
export function SkipNav() {
  return (
    <a
      href="#main-content"
      className="fixed left-4 top-0 z-[200] -translate-y-full rounded-2xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-extruded transition-transform duration-200 ease-out focus:translate-y-4 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background"
    >
      Skip to main content
    </a>
  );
}
