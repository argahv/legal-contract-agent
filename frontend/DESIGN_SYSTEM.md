# Legal Agent — Flat Design System

> Philosophy: hierarchy through typography, scale, and color blocks. Zero box
> shadows on chrome or surfaces. No backdrop-blur.

---

## Color Tokens

All tokens are defined as HSL channels in `app/globals.css` (`:root` block).
They map to Tailwind via `tailwind.config.ts` so shadcn/Radix components
inherit them automatically.

| Token                    | Light hex  | Role                              |
| ------------------------ | ---------- | --------------------------------- |
| `--background`           | `#FFFFFF`  | Page canvas                       |
| `--foreground`           | `#111827`  | Primary text (gray-900)           |
| `--primary`              | `#3B82F6`  | Primary CTA, active nav, links    |
| `--primary-foreground`   | `#FFFFFF`  | Text on primary bg                |
| `--secondary`            | `#10B981`  | Secondary CTA (emerald)           |
| `--secondary-foreground` | `#FFFFFF`  | Text on secondary bg              |
| `--accent`               | `#F59E0B`  | Accent highlight (amber)          |
| `--accent-foreground`    | `#111827`  | Text on accent bg                 |
| `--muted`                | `#F3F4F6`  | Surface tint, sidebar bg          |
| `--muted-foreground`     | `#6B7280`  | Subdued / secondary text          |
| `--card`                 | `#FFFFFF`  | Card surface (same as bg)         |
| `--border`               | `#E5E7EB`  | Hairline separators               |
| `--input`                | `#F3F4F6`  | Input default background          |
| `--ring`                 | `#3B82F6`  | Focus ring color                  |
| `--destructive`          | `#EF4444`  | Error / destructive action        |

### Risk Level Semantic Colors

Defined in `lib/utils.ts` → `riskLevelTone`. Used by `RiskBadge`.

| Level      | Color family | Semantic meaning           |
| ---------- | ------------ | -------------------------- |
| `LOW`      | Emerald      | Safe / standard            |
| `MEDIUM`   | Amber        | Attention required         |
| `HIGH`     | Orange       | Escalate                   |
| `CRITICAL` | Red          | Block / immediate action   |

---

## Typography

Font: **Outfit** (Google Fonts) loaded via `next/font/google` in `app/layout.tsx`.
Weights loaded: 400, 500, 600, 700, 800.

| Use case          | Weight | Tracking         | Notes                          |
| ----------------- | ------ | ---------------- | ------------------------------ |
| Page headings     | 800    | `-0.02em` tight  | `font-extrabold tracking-tight`|
| Section headings  | 700    | tight            | `font-bold tracking-tight`     |
| Card titles       | 700    | tight            | `font-bold`                    |
| Body text         | 400    | normal           | `font-normal`                  |
| Labels / buttons  | 600    | normal           | `font-semibold`                |
| Micro-labels      | 600    | `tracking-wider` | `uppercase tracking-wider`     |

---

## Spacing

Container: `max-w-7xl` with `px-6` padding.
All internal spacing in multiples of 4 px (Tailwind's default 4-based scale).

---

## Border Radius

| Class         | Value  | Use                              |
| ------------- | ------ | -------------------------------- |
| `rounded-md`  | `6px`  | Small elements, badges           |
| `rounded-lg`  | `8px`  | Cards, buttons, inputs, nav items|
| `rounded-xl`  | `12px` | Icon containers, modal overlays  |

Controlled via `--radius: 0.5rem` in `globals.css`.

---

## Shadows

**None.** The design system uses zero box shadows on surfaces and chrome.

- `shadow-none` is the default everywhere.
- Only exception: Recharts tooltip may use `shadow-tooltip` if needed.
- Hierarchy is established through background color blocks, not elevation.

---

## Motion

```css
transition-all duration-200   /* standard for all interactive elements */
hover:scale-105                /* primary + secondary buttons */
hover:scale-[1.02]             /* interactive cards (group) */
```

`prefers-reduced-motion` media query in `globals.css` disables all scale
transforms and shortens all transition durations to 0.01ms.

---

## Component Conventions

### Button

Variants (in `components/ui/button.tsx`):

| Variant       | Appearance                                      |
| ------------- | ----------------------------------------------- |
| `default`     | Solid blue, `hover:scale-105`                   |
| `secondary`   | Solid emerald, `hover:scale-105`                |
| `outline`     | `border-4` primary color, fills blue on hover   |
| `ghost`       | No bg, muted hover                              |
| `destructive` | Solid red                                       |
| `link`        | Text underline only                             |

Sizes: `sm` (h-8), `default` (h-10), `lg` (h-12), `xl` (h-14), `icon` (h-10 w-10).
Use `lg`/`xl` only for hero CTAs; use `default` for dense table actions.

### Card

Flat — no border, no shadow by default. Hierarchy via background tints:

```tsx
<Card className="bg-muted">           {/* muted tint — sidebar/summary */}
<Card className="bg-blue-50">         {/* primary tint — highlighted */}
<Card className="border border-border"> {/* opt-in hairline border */}
```

Interactive cards: add `group hover:scale-[1.02] transition-all duration-200`.

### Input

- Default: `bg-input` (gray-100), no border.
- Focus: white bg + `border-2 border-primary` + `ring-2 ring-ring ring-offset-2`.

### Badge

Flat color-block badges. `RiskBadge` uses `riskLevelTone` className overrides.
Avoid `variant="outline"` — use `variant="muted"` or semantic tones instead.

---

## Accessibility

1. **Focus rings**: every interactive element has `focus-visible:ring-2 ring-ring ring-offset-2`. Never remove these.
2. **Color contrast**: primary (`#3B82F6`) on white passes AA at normal text. Critical red (`#EF4444`) used with white foreground. Amber/orange used on dark bg.
3. **Motion**: `prefers-reduced-motion` respected globally via `globals.css`.
4. **ARIA**: nav landmarks use `aria-label`. Icon-only elements use `aria-hidden` + visually hidden labels.

---

## Adding New Components

1. Place in `components/ui/` (shared primitives) or `components/<feature>/`.
2. Use `cn()` from `lib/utils` for class merging.
3. No inline shadows — use `bg-*` tints for depth.
4. Use `transition-all duration-200` for hover states.
5. Always include `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`.
6. Reference tokens via Tailwind classes, not hardcoded hex values.
