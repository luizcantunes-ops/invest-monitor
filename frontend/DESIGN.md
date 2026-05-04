# Design System — Finance Connect

## Color Strategy

**Restrained.** Indigo accent (#4F46E5 → oklch 50% 0.22 264) carries primary actions, active states, and selection indicators. All surfaces are tinted minimally toward the same hue for coherence. Semantic tokens (success/danger/warning) are used exclusively for data meaning — not decoration.

### Palette

| Token | OKLCH | Hex approx | Role |
|---|---|---|---|
| `--bg` | oklch(96.5% 0.007 264) | #F4F5F7 | Page background |
| `--surface` | oklch(99.5% 0.004 264) | #FEFEFF | Card / panel base |
| `--surface-2` | oklch(95.5% 0.008 264) | #F0F2F5 | Secondary fills |
| `--text` | oklch(20% 0.012 264) | #111827 | Primary text |
| `--muted` | oklch(52% 0.012 264) | #6B7280 | Labels, captions |
| `--border` | oklch(90% 0.008 264) | #E5E7EB | Dividers, outlines |
| `--accent` | oklch(50% 0.22 264) | #4F46E5 | Primary action, selection |
| `--accent-hover` | oklch(45% 0.22 264) | #4338CA | Hover state |
| `--accent-light` | oklch(95% 0.04 264) | #EEF2FF | Accent fills |
| `--accent-text` | oklch(38% 0.18 264) | #3730A3 | Text on accent-light |
| `--success` | oklch(52% 0.16 155) | #059669 | Positive / gain |
| `--success-bg` | oklch(96% 0.04 155) | #ECFDF5 | Success fill |
| `--success-border` | oklch(85% 0.08 155) | #6EE7B7 | Success outline |
| `--danger` | oklch(50% 0.21 27) | #DC2626 | Negative / loss |
| `--danger-bg` | oklch(97% 0.03 27) | #FEF2F2 | Danger fill |
| `--danger-border` | oklch(85% 0.08 27) | #FECACA | Danger outline |
| `--warning` | oklch(62% 0.17 65) | #D97706 | Caution |
| `--warning-bg` | oklch(97% 0.04 90) | #FFFBEB | Warning fill |
| `--warning-border` | oklch(85% 0.09 80) | #FDE68A | Warning outline |

**Never:** gradient text, neon, high-chroma accents in background fills. Danger/success/warning are for data meaning only — never for visual decoration.

## Typography

**Font:** Inter — single family, no pairing. 5 weights in use: 400, 500, 600, 700, 800.

| Element | Size | Weight | Notes |
|---|---|---|---|
| Body | 14px | 400 | Base, line-height 1.5 |
| Label / caption | 11–12px | 600 | Uppercase + letter-spacing for hierarchy |
| Panel label | 12px | 700 | UPPERCASE, 0.5px tracking |
| Symbol / ticker | 18px | 800 | Letter-spacing -0.3px |
| Price | 26px | 800 | Letter-spacing -0.5px |
| Tab button | 13px | 500 / 600 active | |
| Section label | 11px | 700 | UPPERCASE, 0.7px tracking, var(--muted) |

**Scale ratio:** ~1.15. Compact; product density requires it. No fluid/clamped sizes.

## Shape

```
--radius:    10px   (cards, panels, modals)
--radius-sm:  7px   (badges, inputs, compact elements)
```

Buttons use `--radius-sm` except full-width CTAs.

## Elevation

Two levels only:

```
--shadow-sm   Cards at rest
--shadow      Cards hovered, dropdowns, sticky headers
```

Avoid `box-shadow` for decorative purposes. Shadow = depth only.

## Components

### Card

```css
background: var(--surface);
border: 1px solid var(--border);
border-radius: var(--radius);
box-shadow: var(--shadow-sm);
padding: 20px 24px;
```

State cards (setup/watch/danger) use background tint + border color — **never side-stripe borders.**

### Status badges

Small pills, 99px radius:

- **SETUP:** `--success-bg` + `--success-border` border + `#065F46` text
- **WATCH:** `--warning-bg` + `--warning-border` + `#92400E` text
- **EVITAR:** `--surface` + `--border` + muted text

### Tab navigation

Sticky at `top: 60px` (below navbar). Flat bottom-border indicator only (`border-bottom: 2px solid var(--accent)` on active). No border-radius, no box-shadow.

### Decision strip

5-column grid, 10px gap. Each cell: `--surface` card, 14px padding, muted uppercase label (10.5px / 600) + value (14px / 600).

### Section labels

```css
font-size: 11px; font-weight: 700;
text-transform: uppercase; letter-spacing: .7px;
color: var(--muted);
margin: 28px 0 12px;
```

### Pos-tags (Long Term / Swing)

Pill badges, clickable, trigger filter. Hover: filled with accent color.

## Motion

```
150ms ease-out on hover transitions (shadow, color)
200ms ease-out on card lifts (translateY, shadow)
No layout-property animations
No orchestrated sequences
```

## Layout

- Shell: `min(1280px, calc(100vw - 32px))`, centered
- Tab content: direct children, no wrapping container
- Workspace (Análise de Ativo): CSS grid, side-stack + main columns
- Decision strip: 5-col grid, always visible across all tabs
- Cards: single-column list in Carteira; grid in Day Trade

## Anti-patterns

- `border-left` / `border-right` accents on cards
- Gradient text
- Hero-metric layout (big number + small label + gradient badge)
- Neon or high-chroma status colors
- Cards for everything — use tables for tabular data
