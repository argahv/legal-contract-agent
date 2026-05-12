# Legal Agent — frontend notes

## Design system

- **Typography**: **Plus Jakarta Sans** (`font-display` / headings) and **DM Sans** (`font-sans` / body) via `next/font/google` in `app/layout.tsx`.
- **Radius & elevation**: Neumorphic “soft UI” — cards use `rounded-[32px]` with `shadow-extruded`; wells and inputs use `shadow-inset` / `shadow-inset-deep`. Triggers match `Input` (`rounded-2xl`, 44px min height).
- **Palette**: HSL tokens in `app/globals.css` — cool clay neutrals with a **corporate blue** primary (~`221 83% 53%` light, tuned for dark) aligned to UI/UX Pro Max “Trust & Authority” / Enterprise SaaS guidance; teal `success` for positive states. Semantic chart colors map risk tiers.
- **Risk chroma**: `lib/utils.ts` defines `riskLevelTone` (emerald / amber / orange / red) reused by `RiskBadge`, playbook badges, and charts.

## Data flow & client/server boundary

- **Browser data**: All authenticated REST calls use `apiFetch` (`lib/api/client.ts`), which injects `Authorization: Bearer <accessToken>` from the Zustand store and adds `X-Request-Id` per request.
- **Server routes**: Next handlers in `app/api/auth/`* proxy to the backend using `getPublicApiBaseUrl()` (`lib/env.ts`). Login sets an httpOnly `la_refresh` cookie while the JSON body still returns tokens for the SPA store (intentional for this MVP).
- **Session gate**: `middleware.ts` checks the non-httpOnly marker cookie `la_session` (set/cleared via `lib/session-cookie.ts` with Zustand auth). This aligns Edge protection with localStorage-backed tokens.
- **Dynamic pages**: App area pages export `dynamic = "force-dynamic"` where they depend on runtime auth/API — Next build does not need a live backend.

## Auth handling

- **Login**: Client posts to `/api/auth/login`, persists `accessToken` / `refreshToken` / `user` via `useAuthStore` + `localStorage`, and sets `la_session`.
- **Register**: Calls backend directly (`registerAccount`) and mirrors the same client persistence + cookie marker.
- **Refresh**: `app/api/auth/refresh/route.ts` accepts body or `la_refresh` cookie and proxies to `/api/v1/auth/refresh` (re-sets cookie when rotated).
- **Hydration**: `useAuthHydrated` waits for Zustand persist (`onFinishHydration`) with a 500ms safety timeout so role-gated screens do not flash the wrong state.

## WebSockets (upload / processing)

- Hook: `useContractProgress` (`lib/ws/progress.ts`).
- **URL resolution**: Prefer `NEXT_PUBLIC_WS_URL`; otherwise derive `ws(s)` from `NEXT_PUBLIC_API_URL`.
- **Reconnection**: Exponential backoff capped at 30s, max eight attempts; surfaces last structured payload for UI progress bars.
- **Operational guidance**: In production, terminate TLS at the gateway and use `wss:`; ensure sticky sessions if your progress service is multi-node.

## Accessibility checklist

- **Focus**: Shared primitives (`Button`, `Dialog`, `DropdownMenu`, `Tabs`) use visible `focus-visible:ring` styles (2px ring + offset).
- **Landmarks**: Skip link in root `layout.tsx` targets `#main-content`. Marketing `app/page.tsx`, auth `(auth)/layout.tsx`, and `AppShell` each expose a single `main#main-content` (tabIndex -1 for focus target).
- **Dialogs / sheets**: Radix `DialogTitle` / `DialogDescription` provide required naming; close buttons include `sr-only` text.
- **Progress**: `Progress` exposes `role="progressbar"` with `aria-valuenow/min/max`.
- **Upload**: Dropzone presents an explicit `aria-label` on the file input.

## Testing

- Vitest + Testing Library: `pnpm test` / `npm test` runs `vitest run` with `jsdom`.
- Example coverage: `ClauseCard` rendering and `apiFetch` header/error normalization (`*.test.ts(x)` next to sources).