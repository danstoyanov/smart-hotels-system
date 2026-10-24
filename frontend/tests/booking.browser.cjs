const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const path = require("node:path");
const hotel = require("../../hotel/revisions/royal-crest-demo.v1.json");

const base = process.env.GUEST_TEST_ORIGIN || "http://127.0.0.1:8061";
const screenshots = path.resolve("docs/screenshots");
const selected =
  "/review?room=manor-suite&check_in=2026-11-01&check_out=2026-11-03&guests=2";
const booking = {
  demo: true,
  reference: "DEM-ABCDEF123456",
  room_id: "manor-suite",
  check_in: "2026-11-01",
  check_out: "2026-11-03",
  guests: 2,
  message: "Demo reservation only. This is not a real hotel booking.",
};

function payload(section) {
  return {
    status: "ok",
    demo: true,
    hotel: { name: hotel.name, language: hotel.language, timezone: hotel.timezone },
    data: hotel[section],
  };
}

(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    for (const width of [375, 1440]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      const errors = [];
      let posts = 0;
      let lostResponse = false;
      let committed = false;
      page.on("pageerror", (error) => errors.push(error.message));
      await page.route("**/api/**", (route) => {
        const url = new URL(route.request().url());
        const json = (data, status = 200) => route.fulfill({ json: data, status });
        if (url.pathname === "/api/site")
          return json({ name: hotel.name, language: "en", timezone: hotel.timezone, demo: true });
        if (["rooms", "amenities", "policies"].some((section) => url.pathname === `/api/hotel/${section}`))
          return json(payload(url.pathname.split("/")[3]));
        if (url.pathname === "/api/availability")
          return json({ status: "ok", rooms: [hotel.rooms[0]], nights: 2, timezone: hotel.timezone });
        if (url.pathname === "/api/session") return json({ conversation_id: "demo" });
        if (url.pathname === "/api/history") return json({ conversation_id: "demo", turns: [] });
        if (url.pathname === "/api/bookings" && route.request().method() === "POST") {
          posts += 1;
          committed = true;
          if (lostResponse) return route.abort();
          return json(booking, 201);
        }
        if (url.pathname.startsWith("/api/bookings/by-request/"))
          return json(committed ? booking : { detail: "Not found" }, committed ? 200 : 404);
        if (url.pathname.startsWith("/api/bookings/")) return json(booking);
        return route.abort();
      });

      await page.goto(base);
      await page.getByRole("heading", { name: "Rooms at the manor" }).waitFor();
      await page.getByRole("link", { name: "View room" }).first().click();
      await page.getByRole("heading", { name: "Manor Suite" }).waitFor();
      await page.getByRole("link", { name: "All rooms" }).click();
      await page.getByLabel("Arrival").fill("2026-11-01");
      await page.getByLabel("Departure").fill("2026-11-03");
      await page.getByRole("button", { name: /Check availability/i }).last().click();
      await page.getByRole("link", { name: "Review this stay" }).click();
      await page.getByRole("heading", { name: "Review your selection" }).waitFor();
      assert.equal(posts, 0, "review must not create a booking");
      assert.equal(await page.getByRole("button", { name: "Open concierge chat" }).isVisible(), true);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.screenshot({ path: path.join(screenshots, `sin-65-review-${width}.png`), fullPage: true });
      await page.getByRole("button", { name: "Confirm demo reservation" }).click();
      await page.getByRole("heading", { name: "Your demo reservation" }).waitFor();
      assert.equal(posts, 1);
      await page.getByText("Reference: DEM-ABCDEF123456").waitFor();
      await page.screenshot({ path: path.join(screenshots, `sin-65-confirmed-${width}.png`), fullPage: true });
      await page.reload();
      await page.getByText("Reference: DEM-ABCDEF123456").waitFor();
      assert.equal(posts, 1, "refresh must not send another confirmation");

      const lost = await browser.newPage({ viewport: { width, height: 900 } });
      await lost.route("**/api/**", async (route) => {
        const url = new URL(route.request().url());
        const json = (data, status = 200) => route.fulfill({ json: data, status });
        if (url.pathname === "/api/site") return json({ name: hotel.name, language: "en", timezone: hotel.timezone });
        if (["rooms", "amenities", "policies"].some((section) => url.pathname === `/api/hotel/${section}`))
          return json(payload(url.pathname.split("/")[3]));
        if (url.pathname === "/api/availability") return json({ status: "ok", rooms: [hotel.rooms[0]], nights: 2, timezone: hotel.timezone });
        if (url.pathname === "/api/session") return json({ conversation_id: "demo" });
        if (url.pathname === "/api/history") return json({ conversation_id: "demo", turns: [] });
        if (url.pathname === "/api/bookings" && route.request().method() === "POST") {
          posts += 1;
          committed = true;
          return route.abort();
        }
        if (url.pathname.startsWith("/api/bookings/by-request/")) return json(booking);
        if (url.pathname.startsWith("/api/bookings/")) return json(booking);
        return route.abort();
      });
      committed = false;
      lostResponse = true;
      await lost.goto(base + selected);
      await lost.getByRole("button", { name: "Confirm demo reservation" }).click();
      await lost.getByText("The result is unclear.").waitFor();
      await lost.reload();
      await lost.getByText("Reference: DEM-ABCDEF123456").waitFor();
      assert.equal(posts, 2, "lost response recovery must be read-only");
      assert.deepEqual(errors, []);
      await lost.close();
      await page.close();
      console.log(`${width}px: explicit confirmation, refresh and lost response passed`);
    }
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
