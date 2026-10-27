# Product

<!-- impeccable:product-schema 1 -->

Product context for design work (Impeccable `init`, SIN-92). Visual rules are in
[DESIGN.md](DESIGN.md). Confirmed project choices are in [brief.md](brief.md) and
[PLAN.md](PLAN.md); if this file disagrees with them, they win.

## Platform

web

## Users

- **Primary: a guest of the hotel.** They look at the hotel and its rooms, ask the
  concierge chat questions, search for free rooms for a whole stay and confirm a
  demo reservation. They may use a desktop or a phone.
- **Secondary: people who evaluate the demo** (reviewers, possible employers or
  clients). They follow the same guest journey. Design decisions are made for the
  guest first.

## Product Purpose

A website and AI concierge for one fictional hotel, Royal Crest Manor. A guest can
read about the hotel, get answers that come only from reviewed hotel information,
find rooms that are open for every night of a stay and confirm a clearly labelled
demo reservation. Success means the guest completes this journey without confusion
and never mistakes demo content for a real booking.

## Positioning

The concierge answers only from the hotel information in `hotel/`, shows the sources
it read and says when it does not know something. Availability is checked for the
entire stay, and nothing is reserved until the guest explicitly confirms.

## Operating Context

- Main journey: home page → concierge chat or availability search → room page →
  review page → explicit "Confirm demo reservation" → reservation reference.
- Each browser keeps its own private conversation for 24 hours.
- Hotel dates use the property timezone (Europe/Kyiv), not the guest's or the
  server's timezone.
- The chat streams answers (SSE). Slow, interrupted and failed answers are normal
  states the guest can see.

## Capabilities and Constraints

- One hotel only. Initial guest language: English.
- Static HTML, CSS and browser JavaScript in `frontend/`, served by one FastAPI app.
  No frontend framework or build step.
- Search never holds a room. Only the confirm action on the review page creates a
  demo reservation, and a repeated request does not create a second one.
- Excluded: payments, prices, real hotel integrations, multiple hotels, guest
  accounts, staff inboxes and messaging channels.
- Hotel data is rendered as plain text, never as HTML.
- Room names, amenities, policies and inventory dates are not approved business
  facts. They stay marked as fictional demo data.

## Brand Commitments

- Name: **Royal Crest Manor**, a fictional demo hotel. It is not a claim about a
  real business.
- Voice: warm, calm and precise, like a considerate host at a manor house. Short,
  clear sentences in plain English (B1–B2). The concierge admits when it does not
  know something instead of guessing.
- Every fictional room and every demo reservation is labelled as such ("Fictional
  demo room", "Demo reservation"). These labels are never removed for visual reasons.

## Evidence on Hand

- Hotel facts: `hotel/` (active revision `royal-crest-demo.v3`): two rooms, three
  amenities, six policies and explicit inventory from 1 November 2026 to
  30 June 2027.
- Images: three generated, illustrative photographs in `frontend/assets/images/`
  (`manor-hero.png`, `manor-suite.png`, `garden-room.png`). They are not photographs
  of a real hotel. See [the SIN-64 asset notes](docs/history/sin-64-assets.md).
- Fonts: self-hosted Playfair Display and Manrope in `frontend/assets/fonts/` (OFL).
- **Not available, and must not be invented:** prices, guest reviews or ratings,
  awards, press, testimonials, contact details, addresses, staff names, newsletter,
  social accounts and any number that is not in `hotel/`.

## Product Principles

1. **Truth over decoration.** Show only facts from `hotel/` and the backend. An
   empty space is better than an invented claim.
2. **Demo is always visible.** The guest can always tell that the hotel, rooms and
   reservations are fictional.
3. **The guest stays in control.** Nothing is reserved without a clear, explicit
   confirmation, and every failure allows a safe retry.
4. **Calm clarity.** Each screen helps the guest take the next step without noise.

## Accessibility & Inclusion

- Keyboard access, visible focus, labelled form fields and a correct heading order
  are required on every page (kept since SIN-64 and SIN-89).
- The journey must work from 375 px phones to 1440 px desktops.
