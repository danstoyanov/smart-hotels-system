const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const hotel = require("../../hotel/revisions/royal-crest-demo.v1.json");

const base = process.env.GUEST_TEST_ORIGIN || "http://127.0.0.1:8061";
const screenshots = path.resolve(".local/screenshots");
fs.mkdirSync(screenshots, { recursive: true });

function payload(section) {
  return {
    status: "ok",
    demo: true,
    source: { source_id: hotel.source_id, version: hotel.version, demo: true },
    hotel: {
      name: hotel.name,
      language: hotel.language,
      timezone: hotel.timezone,
    },
    section,
    data: hotel[section],
  };
}
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    for (const width of [375, 768, 1440]) {
      const page = await browser.newPage({
        viewport: { width, height: 900 },
        deviceScaleFactor: 1,
      });
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      page.on("console", (msg) => {
        if (msg.type() === "error") errors.push(msg.text());
      });
      await page.route("**/api/**", (route) => {
        const url = new URL(route.request().url());
        const section = url.pathname.split("/")[3];
        const json = (data) => route.fulfill({ json: data });
        if (url.pathname === "/api/site")
          return json({
            name: hotel.name,
            language: hotel.language,
            timezone: hotel.timezone,
            demo: true,
            assistant_mode: "stub",
          });
        if (url.pathname === "/api/hotel/rooms") return json(payload("rooms"));
        if (url.pathname === "/api/hotel/amenities")
          return json(payload("amenities"));
        if (url.pathname === "/api/hotel/policies")
          return json(payload("policies"));
        if (url.pathname === "/api/session")
          return json({ conversation_id: "fixture" });
        if (url.pathname === "/api/history")
          return json({ conversation_id: "fixture", turns: [] });
        if (
          url.pathname === "/api/availability" &&
          url.searchParams.get("check_in") === "2026-11-05"
        )
          return json({ status: "no_match", rooms: [] });
        if (
          url.pathname === "/api/availability" &&
          url.searchParams.get("check_in") === "2026-11-06"
        )
          return route.fulfill({
            status: 503,
            json: {
              status: "unavailable",
              message: "Availability is unavailable. Try again later.",
            },
          });
        if (url.pathname === "/api/availability")
          return json({
            status: "ok",
            demo: true,
            rooms: [hotel.rooms[0]],
            nights: 2,
            timezone: hotel.timezone,
            check_in: "2026-11-01",
            check_out: "2026-11-03",
            guests: 2,
            message:
              "Fictional demo inventory. Search does not reserve or hold a room.",
          });
        if (url.pathname === "/api/conversation")
          return json({ conversation_id: "fixture-new" });
        return route.abort();
      });
      await page.goto(base);
      await page.getByRole("heading", { name: "Rooms at the manor" }).waitFor();
      assert.equal(await page.locator(".room-card").count(), 2);
      assert.equal(await page.locator(".fact-card").count(), 3);
      assert.equal(await page.locator(".policy-card").count(), 6);
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
        true,
        `horizontal overflow at ${width}px`,
      );
      await page.locator(".room-card img").last().scrollIntoViewIfNeeded();
      await page.waitForFunction(() =>
        [...document.querySelectorAll(".room-card img")].every(
          (image) => image.complete && image.naturalWidth > 0,
        ),
      );
      assert.equal(await page.locator("#message").isEnabled(), true);
      const launcher = page.getByRole("button", { name: "Open concierge chat" });
      assert.equal(await launcher.isVisible(), true);
      assert.equal(await page.locator("#chat").isVisible(), false);
      assert.equal(await launcher.locator(".launcher-bubble").textContent(), "Ask");
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      assert.equal(await launcher.isVisible(), true);
      await page.evaluate(() => window.scrollTo(0, 0));
      if (width === 375 || width === 1440) {
        await page.screenshot({
          path: path.join(screenshots, `sin-64-${width}.png`),
          fullPage: true,
        });
      }
      await launcher.focus();
      await page.keyboard.press("Enter");
      assert.equal(await page.locator("#chat").isVisible(), true);
      assert.equal(await page.locator("#message").evaluate((element) => element === document.activeElement), true);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      if (width === 375 || width === 1440) {
        await page.screenshot({
          path: path.join(screenshots, `sin-64-chat-${width}.png`),
        });
      }
      await page.keyboard.press("Escape");
      assert.equal(await page.locator("#chat").isVisible(), false);
      assert.equal(await launcher.evaluate((element) => element === document.activeElement), true);
      await page.reload();
      await page.getByRole("heading", { name: "Rooms at the manor" }).waitFor();
      await page.keyboard.press("Tab");
      assert.equal(
        await page.evaluate(() => document.activeElement?.className),
        "skip-link",
      );
      await page.getByRole("link", { name: "View room" }).first().focus();
      await page.keyboard.press("Enter");
      await page.getByRole("heading", { name: "Manor Suite" }).waitFor();
      await page.waitForFunction(() => {
        const image = document.querySelector(".detail-photo img");
        return image && image.complete && image.naturalWidth > 0;
      });
      assert.equal(
        await page
          .locator(".detail-photo img")
          .evaluate((image) => image.complete && image.naturalWidth > 0),
        true,
      );
      await page.getByRole("link", { name: "All rooms" }).click();
      await page.getByLabel("Arrival").fill("2026-11-01");
      await page.getByLabel("Departure").fill("2026-11-03");
      await page
        .getByRole("button", { name: /Check availability/i })
        .last()
        .click();
      await page.getByRole("link", { name: "Review this stay" }).waitFor();
      await page.getByRole("link", { name: "Review this stay" }).click();
      await page
        .getByRole("heading", { name: "Review your selection" })
        .waitFor();
      await page.getByText("No price or currency is set.").waitFor();
      if (width === 1440) {
        await page.screenshot({
          path: path.join(screenshots, "sin-64-review.png"),
          fullPage: true,
        });
      }
      assert.equal(
        await page
          .getByRole("button", { name: /confirm|reserve|book now/i })
          .count(),
        0,
      );
      await page.goto(base);
      await page.getByLabel("Arrival").fill("2026-11-05");
      await page.getByLabel("Departure").fill("2026-11-07");
      await page
        .getByRole("button", { name: /Check availability/i })
        .last()
        .click();
      await page.getByText("No room is available for the full stay").waitFor();
      assert.deepEqual(errors, [], `console errors at ${width}px`);
      await page.getByLabel("Arrival").fill("2026-11-06");
      await page
        .getByRole("button", { name: /Check availability/i })
        .last()
        .click();
      await page
        .getByText("Availability is unavailable. Try again later.")
        .waitFor();
      assert.equal(errors.length, 1);
      assert.match(errors[0], /503 \(Service Unavailable\)/);
      await page.close();
      console.log(
        `${width}px: rooms, assets, chat, search, review, keyboard and console passed`,
      );
    }
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
