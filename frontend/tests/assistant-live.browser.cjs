// Opt-in real API/model check. Run only after explicit approval for paid calls.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
  if (process.env.APPROVED_LIVE_BROWSER !== 'true') throw new Error('Paid-call approval required');
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const origin = process.env.CHAT_TEST_ORIGIN || 'http://127.0.0.1:8073';
    await page.goto(origin);
    await page.waitForFunction(() => !document.querySelector('#send').disabled);
    await page.getByLabel('Your message', { exact: true }).fill('When can I check in and check out?');
    await page.getByRole('button', { name: 'Send message' }).click();
    await page.getByText('Reply saved.', { exact: false }).waitFor({ timeout: 100000 });
    const history = await page.evaluate(async () => (await fetch('/api/history')).json());
    assert.equal(history.turns.length, 1);
    assert.ok(history.turns[0].answer.length > 0);
    assert.ok(history.turns[0].sources.length > 0);
    const source = history.turns[0].sources[0];
    const response = await page.request.get(origin + source.url);
    assert.equal(response.status(), 200);
    assert.equal((await response.json()).source.version, source.version);
    await page.reload();
    await page.waitForFunction(() => !document.querySelector('#send').disabled);
    assert.equal(await page.locator('#chat-log a').count(), history.turns[0].sources.length);
    for (const [name, viewport] of [['desktop', { width: 1440, height: 1200 }], ['mobile', { width: 390, height: 844 }]]) {
      await page.setViewportSize(viewport);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `docs/screenshots/sin-62-live-${name}.png`, fullPage: true });
    }
    await page.getByRole('button', { name: 'New conversation' }).click();
    await page.getByText('New conversation ready.', { exact: false }).waitFor();
    assert.equal(await page.locator('.chat-message').count(), 0);
    assert.deepEqual(errors, []);
    fs.writeFileSync('docs/sin-62-live-browser.json', JSON.stringify({
      mode: 'real Vertex API, no fixtures', model: 'gemini-3.8-flash',
      turns: history.turns.map(({ question, answer, sources }) => ({ question, answer, sources })),
      checks: ['send', 'saved answer and sources', 'source route', 'refresh', 'desktop', 'mobile', 'reset', 'no page errors'],
    }, null, 2));
    console.log('Real browser journey passed; one live answer, saved sources, refresh, source route, desktop/mobile and reset.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
