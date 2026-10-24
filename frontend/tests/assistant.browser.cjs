// Controlled API fixtures verify UI states. They are not live Gemini evidence.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    fs.mkdirSync('docs/screenshots', { recursive: true });
    for (const [name, viewport] of [['desktop', { width: 1440, height: 1200 }], ['mobile', { width: 390, height: 844 }]]) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      let turns = [];
      let failure = false;
      const source = { title: 'Arrival and departure', version: 1,
        url: '/api/hotel/policies/arrival?source_id=royal-crest-demo&version=1' };
      await page.route('**/api/**', async route => {
        const path = new URL(route.request().url()).pathname;
        const json = data => route.fulfill({ json: data });
        if (path === '/api/site') return json({ name: 'Royal Crest Manor', assistant_mode: 'vertex', timezone: 'Europe/Kyiv' });
        if (path === '/api/health') return json({ status: 'ok' });
        if (path === '/api/session') return json({ conversation_id: 'fixture' });
        if (path === '/api/history') return json({ turns });
        if (path === '/api/conversation') { turns = []; return json({ conversation_id: 'new-fixture' }); }
        if (path === '/api/chat') {
          if (failure) return route.fulfill({ contentType: 'text/event-stream', body:
            'event: error\ndata: {"message":"Reply interrupted. Reload history, then try again."}\n\n' });
          const { message: question, turn_id } = route.request().postDataJSON();
          const answer = 'At our fictional demo hotel, check-in starts at 15:00 and checkout is by 11:00 (Europe/Kyiv). Early check-in and late checkout need staff confirmation.';
          const sources = [source, { title: '<script>unsafe</script>', url: 'javascript:alert(1)' }];
          turns.push({ question, answer, turn_id, sources });
          return route.fulfill({ contentType: 'text/event-stream', body:
            `event: turn_started\ndata: {}\n\nevent: result\ndata: ${JSON.stringify({ answer, sources })}\n\nevent: done\ndata: {}\n\n` });
        }
        return route.abort();
      });
      await page.goto(process.env.CHAT_TEST_ORIGIN || 'http://127.0.0.1:8072');
      await page.waitForFunction(() => !document.querySelector('#send').disabled);
      await page.getByLabel('Your message', { exact: true }).fill('When can I check in and check out?');
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.getByText('Reply saved.', { exact: false }).waitFor();
      assert.equal(await page.locator('#chat-log a').count(), 1);
      assert.equal(await page.locator('#chat-log a').getAttribute('href'), source.url);
      await page.reload();
      await page.waitForFunction(() => !document.querySelector('#send').disabled);
      assert.equal(await page.locator('#chat-log a').count(), 1);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `docs/screenshots/sin-62-${name}.png`, fullPage: true });
      failure = true;
      await page.getByLabel('Your message', { exact: true }).fill('A failed question');
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.getByText('Reply interrupted. Reload history, then try again.', { exact: true }).waitFor();
      assert.equal(await page.locator('.chat-message').count(), 2);
      failure = false;
      await page.getByLabel('Your message', { exact: true }).fill('<img src=x onerror=alert(1)>');
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.getByText('Reply saved.', { exact: false }).waitFor();
      assert.equal(await page.locator('#chat-log img').count(), 0);
      await page.getByRole('button', { name: 'New conversation' }).click();
      await page.getByText('New conversation ready.', { exact: false }).waitFor();
      assert.equal(await page.locator('#chat-log a').count(), 0);
      assert.deepEqual(errors, []);
      console.log(`${name}: saved sources, refresh, safe links/text, failure/retry, reset and overflow passed`);
      await context.close();
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
