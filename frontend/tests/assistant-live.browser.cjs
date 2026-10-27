// Opt-in real API/model check. Run only after explicit approval for paid calls.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
  if (process.env.APPROVED_LIVE_BROWSER !== 'true') throw new Error('Paid-call approval required');
  const started = Date.now();
  let submitted = 0;
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
      if (request.method() === 'POST' && new URL(request.url()).pathname === '/api/chat') submitted++;
    });
    const origin = process.env.CHAT_TEST_ORIGIN || 'http://127.0.0.1:8073';
    await page.goto(origin);
    await page.waitForFunction(() => !document.querySelector('#send').disabled);
    await page.getByRole('button', { name: 'Open concierge chat' }).click();
    await page.getByLabel('Your message', { exact: true }).fill('Is breakfast included and when is it served?');
    await page.getByRole('button', { name: 'Send message' }).click();
    await page.waitForFunction(() => /Reply saved|Reply interrupted|session expired/i.test(
      document.querySelector('#chat-status').textContent), {}, { timeout: 100000 });
    const status = await page.locator('#chat-status').textContent();
    if (!status.startsWith('Reply saved.')) {
      fs.writeFileSync('.local/sin-62-final-browser-failure.json', JSON.stringify({ status }));
      await page.screenshot({ path: '.local/sin-62-final-browser-failure.png', fullPage: true });
      throw new Error(status);
    }
    const history = await page.evaluate(async () => (await fetch('/api/history')).json());
    assert.equal(history.turns.length, 1);
    assert.ok(history.turns[0].answer.length > 0);
    assert.equal(submitted, 1);
    assert.match(history.turns[0].answer, /breakfast/i);
    assert.match(history.turns[0].answer, /included/i);
    assert.match(history.turns[0].answer, /(?:0?7:00|7\s*a\.?m\.?)/i);
    assert.match(history.turns[0].answer, /(?:10:00|10\s*a\.?m\.?)/i);
    assert.ok(history.turns[0].sources.length > 0);
    assert.ok((await page.locator('#chat-log').textContent()).includes(history.turns[0].answer));
    const source = history.turns[0].sources.find(item => /breakfast/i.test(item.title));
    assert.ok(source, 'Breakfast source must be shown');
    assert.match(source.url, /\/api\/hotel\/amenities\/breakfast\?/);
    const response = await page.request.get(origin + source.url);
    assert.equal(response.status(), 200);
    assert.equal((await response.json()).source.version, source.version);
    await page.reload();
    await page.waitForFunction(() => !document.querySelector('#send').disabled);
    await page.getByRole('button', { name: 'Open concierge chat' }).click();
    assert.equal(await page.locator('#chat-log a').count(), history.turns[0].sources.length);
    const restored = await page.evaluate(async () => (await fetch('/api/history')).json());
    assert.deepEqual(restored.turns, history.turns);
    assert.ok((await page.locator('#chat-log').textContent()).includes(history.turns[0].answer));
    assert.deepEqual(await page.locator('#chat-log a').evaluateAll(links => links.map(link => link.getAttribute('href'))), history.turns[0].sources.map(item => item.url));
    assert.equal(submitted, 1);
    for (const [name, viewport] of [['desktop', { width: 1440, height: 1200 }], ['mobile', { width: 390, height: 844 }]]) {
      await page.setViewportSize(viewport);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `.local/screenshots/sin-62-final-live-${name}.png`, fullPage: true });
    }
    await page.getByRole('button', { name: 'New conversation' }).click();
    await page.getByText('New conversation ready.', { exact: false }).waitFor();
    assert.equal(await page.locator('.chat-message').count(), 0);
    assert.deepEqual(errors, []);
    fs.writeFileSync('docs/sin-62-live-browser.json', JSON.stringify({
      mode: 'real Vertex API, no fixtures', model: 'gemini-3.8-flash',
      transport: 'aiohttp', user_requests: submitted, max_model_calls: 8, automatic_retries: false,
      elapsed_seconds: (Date.now() - started) / 1000,
      turns: history.turns.map(({ question, answer, sources }) => ({ question, answer, sources })),
      checks: ['send', 'saved answer and sources', 'source route', 'refresh', 'desktop', 'mobile', 'reset', 'no page errors'],
    }, null, 2));
    console.log('Real browser journey passed; one live answer, saved sources, refresh, source route, desktop/mobile and reset.');
  } finally { await browser.close(); }
})().catch(error => {
  fs.writeFileSync('docs/sin-62-final-browser-failure.json', JSON.stringify({
    outcome: 'failed', name: error.name, message: error.message, stack: error.stack,
  }, null, 2));
  console.error(error); process.exitCode = 1;
});
