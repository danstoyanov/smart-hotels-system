const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const origin = process.env.GUEST_TEST_ORIGIN || 'http://127.0.0.1:8000';
const screenshots = path.resolve('.local/screenshots');
fs.mkdirSync(screenshots, { recursive: true });

async function run(width, dates, keyboard) {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  const errors = [];
  let bookingPosts = 0;
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (new URL(request.url()).pathname === '/api/bookings' && request.method() === 'POST') bookingPosts += 1;
  });
  try {
    await page.goto(origin);
    await page.getByRole('heading', { name: 'Rooms at the manor' }).waitFor();
    await page.getByRole('button', { name: 'Open concierge chat' }).click();
    await page.getByLabel('Your message').fill('What time is breakfast?');
    await page.getByRole('button', { name: 'Send message' }).click();
    await page.getByText('This is a demo reply.', { exact: false }).waitFor();
    await page.getByRole('button', { name: 'Close concierge chat' }).click();
    await page.getByLabel('Arrival').fill(dates[0]);
    await page.getByLabel('Departure').fill(dates[1]);
    await page.getByRole('button', { name: /Check availability/i }).last().click();
    await page.getByRole('link', { name: 'Review this stay' }).first().waitFor();
    await page.getByRole('link', { name: 'View room' }).first().click();
    await page.getByRole('heading', { name: 'Manor Suite' }).waitFor();
    await page.goto(origin + '/');
    await page.getByLabel('Arrival').fill(dates[0]);
    await page.getByLabel('Departure').fill(dates[1]);
    await page.getByRole('button', { name: /Check availability/i }).last().click();
    await page.getByRole('link', { name: 'Review this stay' }).first().click();
    await page.getByRole('heading', { name: 'Review your selection' }).waitFor();
    assert.equal(bookingPosts, 0, 'review must be read-only');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(screenshots, `sin-67-review-${width}.png`), fullPage: true });
    const confirm = page.getByRole('button', { name: 'Confirm demo reservation' });
    if (keyboard) {
      await confirm.focus();
      assert.equal(await confirm.evaluate(el => el === document.activeElement), true);
      await page.keyboard.press('Enter');
    } else {
      await confirm.click();
    }
    await page.getByRole('heading', { name: 'Your demo reservation' }).waitFor();
    assert.equal(bookingPosts, 1, 'confirmation must send one booking request');
    const reference = await page.locator('.booking-reference').textContent();
    assert.match(reference, /^Reference: DEM-/);
    await page.screenshot({ path: path.join(screenshots, `sin-67-confirmed-${width}.png`), fullPage: true });
    await page.reload();
    await page.getByText(reference).waitFor();
    assert.equal(bookingPosts, 1, 'refresh must not send another confirmation');
    const owned = await page.request.get(`${origin}/api/bookings/${reference.replace('Reference: ', '')}`);
    assert.equal(owned.status(), 200);
    const stranger = await browser.newContext();
    const denied = await stranger.request.get(`${origin}/api/bookings/${reference.replace('Reference: ', '')}`);
    assert.equal(denied.status(), 401);
    await stranger.close();
    assert.deepEqual(errors, []);
    console.log(`${width}px: stub question, availability, room, review, confirmation, owned lookup, refresh passed${keyboard ? ' by keyboard' : ''}`);
  } finally {
    await browser.close();
  }
}

(async () => {
  await run(1440, ['2026-11-01', '2026-11-03'], true);
  await run(375, ['2026-11-03', '2026-11-05'], false);
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto(origin);
    const unknown = await page.request.get(`${origin}/api/hotel/policies/prices`);
    assert.equal((await unknown.json()).status, 'unknown');
    await page.getByLabel('Arrival').fill('2026-11-06');
    await page.getByLabel('Departure').fill('2026-11-08');
    await page.getByLabel('Guests').fill('5');
    await page.getByRole('button', { name: /Check availability/i }).last().click();
    await page.getByText('No room is available for the full stay and guest count.').waitFor();
    await page.getByLabel('Arrival').fill('2026-11-08');
    await page.getByLabel('Departure').fill('2026-11-10');
    await page.getByLabel('Guests').fill('2');
    await page.getByRole('button', { name: /Check availability/i }).last().click();
    await page.getByText('Inventory is unknown for at least one suitable room on these dates.').waitFor();
    await page.getByLabel('Arrival').fill('2026-11-06');
    await page.getByLabel('Departure').fill('2026-11-08');
    await page.getByLabel('Guests').fill('2');
    await page.getByRole('button', { name: /Check availability/i }).last().click();
    await page.getByRole('link', { name: 'Review this stay' }).first().click();
    let savedRequest;
    let committed;
    await page.route('**/api/bookings', async route => {
      savedRequest = route.request().postDataJSON();
      committed = await route.fetch();
      await route.abort();
    });
    await page.getByRole('button', { name: 'Confirm demo reservation' }).click();
    await page.getByText('The result is unclear.').waitFor();
    assert.equal(committed.status(), 201);
    await page.reload();
    await page.getByRole('heading', { name: 'Your demo reservation' }).waitFor();
    const reference = (await page.locator('.booking-reference').textContent()).replace('Reference: ', '');
    await page.unroute('**/api/bookings');
    const replay = await page.request.post(`${origin}/api/bookings`, {
      headers: { Origin: origin }, data: savedRequest,
    });
    assert.equal(replay.status(), 200);
    assert.equal((await replay.json()).reference, reference);
    console.log('Unknown policy, no matching room, unknown dates, lost response, recovery and same-request replay passed');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
