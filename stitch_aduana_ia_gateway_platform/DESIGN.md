---
name: Sovereign Precision
colors:
  surface: '#fbf8ff'
  surface-dim: '#dad9e3'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f2fd'
  surface-container: '#eeedf7'
  surface-container-high: '#e8e7f1'
  surface-container-highest: '#e3e1ec'
  on-surface: '#1a1b22'
  on-surface-variant: '#464555'
  inverse-surface: '#2f3038'
  inverse-on-surface: '#f1effa'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#684000'
  on-tertiary: '#ffffff'
  tertiary-container: '#885500'
  on-tertiary-container: '#ffd4a4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#fbf8ff'
  on-background: '#1a1b22'
  surface-variant: '#e3e1ec'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2.5rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system embodies modern executive governance: restrained, authoritative, and impeccably organized. Designed for customs officials, trade analysts, and cross-border enterprise operators, the interface replaces archaic bureaucratic density with an expansive, noise-free workspace. 

The aesthetic is ultra-clean minimalism anchored by hairline structural boundaries, generous spatial padding, and purposeful typography. Interactions feel quiet and instantaneous—evoking absolute legal compliance, analytical precision, and institutional confidence without decorative distraction.

## Colors
The palette leverages a high-clarity neutral axis framed by crisp hairline borders, punctuated by functional status accents.

- **Light Mode Canvas & Surfaces**: Pure white canvas (`#FFFFFF`) with secondary tier cards in soft neutral tint (`#FAFAFA`) and interactive hover states (`#F4F4F5`). Structural dividers and boundaries utilize hairline zinc (`#E4E4E7`).
- **Dark Mode Canvas & Surfaces**: Deep matte black base (`#0A0A0A`) with charcoal containers (`#121212`) and elevated flyouts (`#18181B`). Structural dividers switch to muted zinc (`#27272A`).
- **Brand & Semantic Accents**:
  - Primary Action / Focus: Muted Indigo (`#4F46E5` in light mode, `#6366F1` in dark mode).
  - Clearance / Verified: Emerald Green (`#10B981`).
  - Flagged / Review Required: Amber (`#F59E0B`).
  - Critical Audit / Blocked: Crimson Red (`#EF4444`).
- **Text Hierarchies**: Primary text commands high contrast (`#09090B` light / `#F4F4F5` dark), secondary text provides context (`#71717A` light / `#A1A1AA` dark), and tertiary text manages metadata (`#A1A1AA` light / `#52525B` dark).

## Typography
Typography is split strictly into two roles:
1. **Inter** powers natural-language layouts, navigation, and executive summaries. Weights stay restricted to 400 (regular), 500 (medium), and 600 (semi-bold) to preserve editorial lightness.
2. **JetBrains Mono** governs all technical, legal, and transactional data: Harmonized Tariff System (HS) codes, declaration IDs, cryptographic validation hashes, timestamps, and masked credentials. Numbers rendered in JetBrains Mono align tabularly by default for scanning dense audit ledgers.

## Layout & Spacing
The layout adheres to a 12-column fluid grid system with expansive boundary constraints.
- **Desktop (1280px+)**: 12 columns, 24px gutters, 40px outer canvas margins. Maximizes vertical white space between functional segments to isolate decision-making units.
- **Tablet (768px - 1279px)**: 8 columns, 20px gutters, 28px outer margins. Data panels collapse from three columns to two.
- **Mobile (< 768px)**: 4 columns, 16px gutters, 20px margins. Multi-column data inspection grids convert to single-column stacked dossiers.

Internal component breathing room strictly enforces `space-md` (16px) or `space-lg` (24px) padding to prevent visual crowding in dense compliance workflows.

## Elevation & Depth
Depth is realized through surface tonality and hairline boundaries rather than heavy drop shadows:
- **Baseline Tier**: Surfaces maintain flat placement, outlined by a 1px hairline border (`#E4E4E7` light / `#27272A` dark).
- **Cards & Data Groups**: Set on `#FAFAFA` (light) or `#121212` (dark) with 1px border. No drop shadow is used under neutral state.
- **Floating Overlays & Menus**: Elevated inspection popovers, command palettes, and filter dropdowns apply a subtle ambient shadow: `0 8px 30px rgba(0, 0, 0, 0.04)` in light mode, and `0 8px 30px rgba(0, 0, 0, 0.40)` with border `#27272A` in dark mode.
- **Backdrop Diffusion**: Modal sheets and full-screen drawers utilize a clean backdrop wash (`rgba(255, 255, 255, 0.8)` or `rgba(10, 10, 10, 0.8)`) with `backdrop-filter: blur(12px)`.

## Shapes
Geometry uses clean, controlled soft radii that maintain a contemporary executive finish without skewing overly playful.
- Standard interactive elements (buttons, inputs, select triggers, code badges) leverage an 8px (`rounded-md` to 12px `rounded-lg`) corner curvature.
- Content containers, audit tables, and dossier cards employ a consistent 12px to 16px radius (`rounded-lg` / `rounded-xl`).
- Micro status dots and circular avatars preserve full geometric pills (`rounded-full`).

## Components

### Buttons
- **Primary**: Solid Indigo (`#4F46E5` / `#6366F1`) with crisp white typography. Height 40px, padding horizontal 16px, 10px corner radius.
- **Secondary**: Surface matching canvas with 1px hairline border (`#E4E4E7` / `#27272A`), hover background `#F4F4F5` / `#18181B`. Text is primary neutral.
- **Ghost**: Zero border, transparent surface, shifts to neutral wash on hover for low-friction actions (e.g., table row menu triggers).

### Chips & Badges
- **Status Tags**: Semi-transparent tinted backgrounds (`8%` opacity of status hex) with solid text and an optional 6px circular indicator dot. E.g., Cleared uses `#10B981` at 10% fill with solid emerald text. Height 24px, 6px radius.
- **HS Code / Hash Badges**: Styled in `JetBrains Mono`, subtle background tint, border 1px solid hairline, displaying reference numbers with letter-spacing.

### Data Inputs & Search Fields
- 40px height, inset padding horizontal 12px. Hairline border `#E4E4E7` / `#27272A`.
- Active focus state changes border to primary Indigo with a crisp 1px optical ring (`box-shadow: 0 0 0 1px #4F46E5`), without fuzzy outer glow. Placeholder text in muted `#A1A1AA`.

### Checkboxes & Radios
- 16px square or circular boxes with 1px border. Checked state renders solid Indigo with a sharp 1.5px white checkmark icon.

### Cards & Dossiers
- Framed by a 1px continuous hairline outline. Padding is generous (24px internal). Headers separate from body content with a matching 1px horizontal rule, avoiding drop shadows entirely.

### Specialized GovTech Components
- **Declaration Stream Row**: Interactive multi-attribute table row containing consignment ID (monospace), country flags, tariff code pill, AI confidence score meter, and status indicator, padded at 16px vertical cadence for comfortable verification.
- **Diff / Audit Inspector**: Side-by-side verification block utilizing red/green surface fills (`5%` opacity) with monospace highlights for customs cargo manifest discrepancy checking.