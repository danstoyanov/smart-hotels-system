---
name: Royal Manor Estate
colors:
  surface: '#fcf9f4'
  surface-dim: '#dcdad5'
  surface-bright: '#fcf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3ee'
  surface-container: '#f0ede9'
  surface-container-high: '#ebe8e3'
  surface-container-highest: '#e5e2dd'
  on-surface: '#1c1c19'
  on-surface-variant: '#424844'
  inverse-surface: '#31302d'
  inverse-on-surface: '#f3f0eb'
  outline: '#727974'
  outline-variant: '#c2c8c3'
  surface-tint: '#4c6358'
  primary: '#051b12'
  on-primary: '#ffffff'
  primary-container: '#1a3026'
  on-primary-container: '#80988b'
  inverse-primary: '#b3ccbe'
  secondary: '#735c00'
  on-secondary: '#ffffff'
  secondary-container: '#fed65b'
  on-secondary-container: '#745c00'
  tertiary: '#221501'
  on-tertiary: '#ffffff'
  tertiary-container: '#39290f'
  on-tertiary-container: '#a88f6e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cfe9d9'
  primary-fixed-dim: '#b3ccbe'
  on-primary-fixed: '#092016'
  on-primary-fixed-variant: '#354c40'
  secondary-fixed: '#ffe088'
  secondary-fixed-dim: '#e9c349'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#fbdeb8'
  tertiary-fixed-dim: '#dec29e'
  on-tertiary-fixed: '#271903'
  on-tertiary-fixed-variant: '#574428'
  background: '#fcf9f4'
  on-background: '#1c1c19'
  surface-variant: '#e5e2dd'
typography:
  display:
    fontFamily: Playfair Display
    fontSize: 56px
    fontWeight: '600'
    lineHeight: 64px
    letterSpacing: -0.02em
  display-mobile:
    fontFamily: Playfair Display
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Playfair Display
    fontSize: 28px
    fontWeight: '500'
    lineHeight: 36px
  headline-sm:
    fontFamily: Playfair Display
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 30px
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Manrope
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Manrope
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Manrope
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.08em
  label-md:
    fontFamily: Manrope
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.12em
  caption:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an ultra-luxury hospitality experience at the intersection of European grand manor heritage and modern Apple HIG-inspired Liquid Glass interface design. Built for high-net-worth travelers, bespoke retreat seekers, and architectural connoisseurs, the aesthetic balances timeless classical grandeur with fluid, tactile digital craftsmanship.

The visual narrative relies on airy composition, rich organic depths, and frosted surfaces that mimic heavy crystal glassware. Interactivity feels effortless, soft-damped, and physical—combining translucent floating sheets, optical specular glints, precise hairline boundaries, and editorial typography that evokes private estate stationery.

## Colors

The color palette translates organic estate landscapes and warm golden-hour tones into a digital canvas:

- **Primary (`#1A3026` / Deep Canopy Green):** Anchors navigation panels, authoritative typography, and deep structural surfaces. Communicates timeless botanical majesty.
- **Secondary (`#D4AF37` / Antique Gold Leaf):** Used sparingly for badges, premium star ratings, focus indicators, and bespoke micro-interactions.
- **Tertiary (`#E5C9A4` / Champagne Dusk):** Powers primary interactive booking buttons, highlight ribbons, and warm glow gradients.
- **Neutral (`#FAF7F2` / Parchment Cream):** The underlying foundation across the interface, avoiding stark clinical white in favor of soft, tangible stationery tones.
- **Charcoal Ink (`#1E2522`):** Primary body and high-contrast text color for optimal optical readability against light backgrounds.

Glass surfaces utilize `rgba(255, 255, 255, 0.65)` layered on light themes and `rgba(26, 48, 38, 0.75)` on dark immersion containers, framed with a 1px perimeter border at `rgba(255, 255, 255, 0.3)`.

## Typography

The type scale pairs high-contrast transitional serifs with a rational geometric sans-serif:

- **Playfair Display** commands the editorial voice. It delivers European manor heritage across hero headlines, section narratives, and suite designations. It is set with tight letter tracking on larger displays to create an intimate, sophisticated cadence.
- **Manrope** delivers crystalline operational legibility for body descriptions, metadata, pricing counters, and reservation inputs.
- **All-Caps Eyebrow Labels:** All `label-lg` and `label-md` tokens are set in uppercase with deliberate letter spacing (+0.08em to +0.12em) to structure section headers like "UNFORGETTABLE MOMENTS" and "STAY IN STYLE".

## Layout & Spacing

The layout is built upon an intentional, rhythm-driven 12-column grid capped at a maximum width of 1360px:

- **Desktop (>= 1024px):** 12 columns with 24px (`1.5rem`) gutters and 32px to 64px outer margins. Bento grids showcase asymmetrical 7/5 or 4/4/4 module splits for amenities and experiences.
- **Tablet (768px – 1023px):** 8 columns with 20px gutters and 24px margins. Cards reflow into paired 2-column sets.
- **Mobile (< 768px):** 4 columns with 16px gutters and 16px margins. Complex reservation modules collapse into stacked vertical cards or sticky bottom sheets.
- **Macro Rhythm:** Generous vertical section spacing (80px to 120px) creates breathing room, evoking unhurried luxury.

## Elevation & Depth

Depth is established via Apple-style Liquid Glass surfaces rather than heavy, opaque shadows:

- **Floating Glass Shelves:** Primary cards and floating docks feature `backdrop-filter: blur(24px) saturate(180%)`, combined with 60% translucent neutral fills.
- **Specular Hairlines:** Elements are bounded by a `1px` translucent border (`rgba(255, 255, 255, 0.4)` on light surfaces; `rgba(255, 255, 255, 0.12)` on dark surfaces) with an inner top highlight `box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6)`.
- **Atmospheric Ambient Drop Shadows:** Shadows are extra-diffuse and warm-tinted rather than neutral black:
  - *Resting card:* `0 12px 32px -4px rgba(26, 48, 38, 0.06), 0 4px 12px -2px rgba(26, 48, 38, 0.03)`
  - *Floating Booking Bar / Dock:* `0 24px 48px -8px rgba(26, 48, 38, 0.14), 0 8px 16px -4px rgba(26, 48, 38, 0.06)`
  - *Hover elevation:* Translates upward by `-2px` with a soft gold edge reflection `0 16px 40px -4px rgba(212, 175, 55, 0.15)`.

## Shapes

The design system embraces fluid Apple-inspired squircles:

- **Large Glass Cards & Bento Containers:** Standardized at `rounded-3xl` (24px to 32px) to soften architectural boundaries and invite exploration.
- **Floating Island Navigation & Booking Bars:** Encased in smooth pill geometries (`rounded-full`) or `rounded-2xl` for segmented modular sections.
- **Input Fields & Sub-Controls:** Radii set to `rounded-xl` (12px to 16px) for an ergonomic, tactile touch target.
- **Imagery:** Media elements follow container squircle masks with a subtle 1px inset optical stroke to prevent wash-out against cream backgrounds.

## Components

### Buttons
- **Primary Reservation Action:** Rich Champagne Dune (`#E5C9A4`) with dark charcoal text (`#1E2522`). Features a smooth hover shift to `#D4AF37` with an ambient glow. Fully pill-shaped (`rounded-full`), uppercase `label-lg` typography.
- **Secondary Manor Action:** Deep Canopy Green (`#1A3026`) fill with cream typography (`#FAF7F2`), paired with a top specular highlight border.
- **Ghost & Glass Buttons:** Frosted backdrop (`backdrop-blur-md`, `bg-white/20`) framed with a 1px border.

### Floating Booking Bar
- Sits suspended over the hero horizon. A consolidated pill island divided into micro-segments: Check-in, Check-out, Guests, and Room Selection.
- Divided by vertical hairline separators (`border-white/20`). Dropdown triggers feature smooth micro-chevron rotation upon interaction.

### Bento Experience & Suite Cards
- **Suite Cards:** Composed of an edge-to-edge photography window at top, wrapped in a 24px squircle frame, descending into a warm cream glass container. Accompanied by pricing locks ("FROM $429 / NIGHT") and discreet pill CTA triggers.
- **Testimonial Pods:** Frosted glass panels displaying warm gold star matrices, custom quotes, and rounded avatar badges.

### Input Fields & Selectors
- Frosted translucent backgrounds with inset padding. Floating labels in `Manrope` uppercase caption typography that transition smoothly on focus. Accent outline radiates subtle champagne gold (`#D4AF37`).

### Floating Island Dock (Navigation)
- Top-anchored floating dock with blurred acrylic transparency, displaying estate crest insignia on the left, centered navigation links with subtle underline indicators, and a persistent "Book Now" CTA pill on the right.