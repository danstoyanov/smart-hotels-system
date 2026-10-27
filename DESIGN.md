---
name: Royal Crest Manor
description: Guest website and concierge for a fictional demo manor hotel.
colors:
  green: "#051b12"
  green-soft: "#1a3026"
  gold: "#ffe088"
  gold-deep: "#735c00"
  gold-focus: "#b18000"
  cream: "#fcf9f4"
  paper: "#f6f3ee"
  white: "#ffffff"
  ink: "#1c1c19"
  muted: "#424844"
  line: "#d8d8d0"
  card-line: "#eee9de"
  error: "#8c281e"
typography:
  display:
    fontFamily: "Playfair Display, Georgia, serif"
    fontSize: "clamp(2.6rem, 5.5vw, 5.1rem)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Playfair Display, Georgia, serif"
    fontSize: "clamp(1.9rem, 3vw, 2.7rem)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Playfair Display, Georgia, serif"
    fontSize: "1.35rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 700
    letterSpacing: "0.1em"
rounded:
  field: "14px"
  photo: "18px"
  chat: "22px"
  card: "28px"
  pill: "999px"
spacing:
  gutter-mobile: "16px"
  gutter: "24px"
  grid-gap: "24px"
  card-padding: "28px"
  section-cta: "96px"
components:
  button-gold:
    backgroundColor: "{colors.gold}"
    textColor: "#241a00"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "13px 23px"
  button-dark:
    backgroundColor: "{colors.green}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "13px 23px"
  button-outline:
    textColor: "{colors.green}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "13px 23px"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.green}"
    rounded: "{rounded.field}"
    height: "50px"
    padding: "0 14px"
  chip:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.green}"
    rounded: "{rounded.pill}"
    padding: "5px 12px 5px 9px"
  room-card:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.card}"
    padding: "28px"
  chat-window:
    backgroundColor: "{colors.cream}"
    rounded: "{rounded.chat}"
    width: "420px"
  chat-window-top:
    backgroundColor: "{colors.green}"
    textColor: "{colors.white}"
    padding: "20px 22px 18px"
---

# Design System: Royal Crest Manor

The visual system as built in `frontend/assets/site.css` (recorded in SIN-92).
Product facts and voice are in [PRODUCT.md](PRODUCT.md). The original design
reference from SIN-64 is kept unchanged in [design/DESIGN.md](design/DESIGN.md);
when the two disagree, this file and `site.css` describe the real site.

## Overview

**Creative North Star: "The Garden Terrace"**

The site feels like stepping onto the stone terrace of a manor at golden hour:
deep canopy green, warm cream stone and a little lantern gold. It is calm and
spacious, with large serif headlines, generous whitespace and photographs that do
the atmospheric work. Nothing shouts. Gold is a small, warm light, not a fill.

Components are soft and restrained: pill-shaped buttons and chips, softly rounded
cards, gentle green-tinted shadows and a slight lift on hover. Glass panels (the
floating navigation and the search panel) sit over the hero photograph like glass
in a garden room. Every fictional room and demo reservation carries a visible
label, and that label is part of the design, not a footnote.

**Key Characteristics:**
- Deep green and warm cream, with gold used sparingly for accents and focus.
- Playfair Display headlines over a quiet Manrope body.
- Pill buttons, 28px cards, soft green shadows, light glass over photographs.
- Calm density: one clear next step per section.

## Colors

A warm, natural palette taken from the garden photographs: green canopy, cream
stone, lantern light.

### Primary
- **Canopy Green** (`green`): headings in brand areas, dark buttons, the chat header,
  the CTA band and the hero overlay. The colour of trust and calm.
- **Deep Canopy** (`green-soft`): secondary dark surfaces next to Canopy Green.

### Secondary
- **Lantern Gold** (`gold`): the primary call to action ("Ask the concierge",
  search), italic hero words and gold text on dark backgrounds.
- **Antique Brass** (`gold-deep`): eyebrows, feature icons and link hover on light
  backgrounds, where Lantern Gold has too little contrast.
- **Focus Amber** (`gold-focus`): the 3px keyboard focus outline only.

### Neutral
- **Manor Cream** (`cream`): the page background and the chat window.
- **Terrace Paper** (`paper`): input fields, chips and policy tags.
- **White** (`white`): room and review cards that sit on Manor Cream.
- **Ink** (`ink`): body text.
- **Moss Grey** (`muted`): secondary text, labels and notes.
- **Stone Line** (`line`) and **Card Edge** (`card-line`): borders and dividers.
- **Brick** (`error`): error notices only.

### Named Rules
**The Lantern Rule.** Lantern Gold is a light, not a wall. Use it for one primary
action per view, small accents and text on green; never for large backgrounds.

**The Brass on Cream Rule.** On light backgrounds, gold text and icons use Antique
Brass, never Lantern Gold, so they stay readable.

## Typography

**Display Font:** Playfair Display (with Georgia, serif)
**Body Font:** Manrope (with Arial, sans-serif)

**Character:** A classic manor-house serif for headlines, paired with a clean,
friendly sans for everything the guest has to read or tap. Both fonts are
self-hosted variable fonts in `frontend/assets/fonts/`.

### Hierarchy
- **Display** (600, fluid 2.6rem–5.1rem, 1.15): the hero `h1` only. Italic words
  in Lantern Gold at weight 400 add warmth.
- **Headline** (600, fluid 1.9rem–2.7rem, 1.15): section `h2` headings.
- **Title** (600, 1.35rem; room titles 1.7rem): card and panel headings.
- **Body** (400, 15px, 1.65): all running text. Paragraphs stop at 65ch.
- **Label** (700, 0.64rem–0.74rem, letter-spacing 0.09em–0.19em, uppercase):
  buttons, navigation, eyebrows, form labels and tags.

### Named Rules
**The One Serif Voice Rule.** Playfair Display is for headings and the brand name
only. Labels, forms, chat messages and notes always use Manrope.

## Layout

- Content sits in a centred column `min(100% - 48px, 1360px)`; on phones the side
  gutter drops to 16px each side.
- Sections stack vertically with generous space; the dark CTA band uses 96px of
  vertical padding.
- Room cards use a two-column grid with a 24px gap; it becomes one column on
  narrow screens. The search form is a four-column grid that stacks on phones.
- Breakpoints: 1100px (tighter navigation), 850px (navigation wraps, grids
  narrow) and 600px (phone layout).
- The floating concierge launcher stays in the bottom-right corner and respects
  safe-area insets.

## Elevation & Depth

A layered system with soft, green-tinted shadows (`rgba(5, 27, 18, …)`) and light
glass. Cards rest on a faint ambient shadow; floating elements (navigation, search
panel, chat window) use deeper, wider shadows. Glass panels combine a translucent
cream or white fill with `backdrop-filter: blur(…)` over photographs. Exact shadow
values are in `.impeccable/design.json`.

### Named Rules
**The Green Shadow Rule.** Shadows are always tinted with Canopy Green, never pure
black, so depth stays warm.

**The Lift on Hover Rule.** Buttons and the chat launcher lift 2–4px on hover. With
`prefers-reduced-motion: reduce`, the lift and transitions are turned off.

## Shapes

Soft and rounded throughout. Buttons, chips, tags and the navigation bar are full
pills (999px). Cards and the search panel use 28px corners, the chat window 22px,
photographs inside cards 18px and form fields 14px. Brand marks and icon buttons
are circles. Icons are thin line icons (18px, 1.6 stroke, round caps).

## Components

### Buttons
- **Shape:** full pill (999px), uppercase Manrope label, 13px × 23px padding.
- **Gold:** Lantern Gold with dark brown text; the main action in a view.
- **Dark:** Canopy Green with white text; strong secondary action on light pages.
- **Outline:** 1px Canopy Green border, transparent fill.
- **Glass:** translucent white with blur, for actions over the hero photograph.
- **Hover / Focus:** 2px lift and a soft green shadow; focus shows the 3px Focus
  Amber outline. Disabled buttons fade to 55% opacity.

### Chips and Tags
- **Style:** Terrace Paper pills with Canopy Green bold text and a small line icon,
  used for room amenities and policy tags.
- **Muted tag:** pale gold fill with Antique Brass text.
- **Photo tags and badges:** dark or cream pills on room photographs, including the
  "Fictional demo room" badge.

### Cards / Containers
- **Corner Style:** 28px.
- **Background:** White on Manor Cream.
- **Shadow Strategy:** faint ambient shadow (see Elevation & Depth).
- **Border:** 1px Card Edge.
- **Internal Padding:** 28px; room cards have a 320px photograph on top and a
  footer row divided by a hairline.

### Inputs / Fields
- **Style:** 50px high, Terrace Paper fill, 1px Stone Line border, 14px corners,
  Canopy Green text. Labels sit above in uppercase Label style.
- **Focus:** 3px Focus Amber outline.
- **Error:** notices under the form turn Brick.

### Navigation
- A floating glass pill over the hero: translucent cream, blur, soft shadow and
  the round brand mark (gold fleur on Canopy Green). Links are uppercase labels
  that turn Antique Brass on hover. Below 850px the bar wraps and its corners
  soften to 25px.

### Concierge Chat (signature component)
- A round gold launcher with a speech bubble in the bottom-right corner opens a
  420px chat window: Canopy Green header, Manor Cream body, messages divided by
  hairlines, a white text area and a privacy note. Messages render as plain text
  and list the hotel sources the concierge read.

## Do's and Don'ts

### Do:
- **Do** use only the colour tokens above; add a new token here before using a
  new colour.
- **Do** keep one Lantern Gold primary action per view.
- **Do** keep the "Fictional demo room" and "Demo reservation" labels visible
  wherever rooms or reservations appear.
- **Do** keep the 3px Focus Amber outline on every interactive element.
- **Do** turn off lifts and transitions under `prefers-reduced-motion: reduce`.

### Don't:
- **Don't** use Lantern Gold for text or icons on cream or white backgrounds.
- **Don't** use pure black shadows or hard, dark drop shadows.
- **Don't** use Playfair Display for labels, form fields or chat messages.
- **Don't** add remote images or fonts; use the three photographs and the
  self-hosted fonts in `frontend/assets/`.
- **Don't** show prices, ratings, awards or contact details as visual decoration.
