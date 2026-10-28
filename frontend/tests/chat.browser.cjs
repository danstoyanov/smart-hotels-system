// UI checks use controlled API fixtures. PostgreSQL tests verify server behavior.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    fs.mkdirSync('.local/screenshots', { recursive: true });
    for (const [name, viewport] of [['desktop', { width: 1440, height: 1200 }], ['mobile', { width: 390, height: 844 }]]) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      let turns = [];
      let mode = 'complete';
      await page.route('**/api/**', async route => {
        const path = new URL(route.request().url()).pathname;
        const json = data => route.fulfill({ json: data });
        if (path === '/api/site') return json({ name: 'Royal Crest Manor', language: 'en', timezone: 'Europe/Kyiv' });
        if (path === '/api/health') return json({ status: 'ok' });
        if (path === '/api/session') return json({ conversation_id: 'fixture' });
        if (path === '/api/history') return json({ conversation_id: 'fixture', turns });
        if (path === '/api/conversation') { turns = []; return json({ conversation_id: 'fixture-new' }); }
        if (path === '/api/chat') {
          const body = route.request().postDataJSON();
          if (mode === 'fail') {
            return route.fulfill({ contentType: 'text/event-stream', body:
              'event: text\ndata: {"text":"not saved"}\n\nevent: error\ndata: {"message":"Demo reply failed. Try again."}\n\n' });
          }
          if (mode === 'hold') {
            await new Promise(resolve => setTimeout(resolve, 1200));
            return route.abort().catch(() => {});
          }
          const answer = 'This is a demo reply. The hotel AI assistant is not connected yet. Your completed messages are saved in this browser session. No reservation has been made.';
          turns.push({ turn_id: body.turn_id, question: body.message, answer });
          return route.fulfill({ contentType: 'text/event-stream', body:
            `event: turn_started\ndata: {}\n\nevent: text\ndata: ${JSON.stringify({ text: answer })}\n\nevent: result\ndata: ${JSON.stringify({ answer })}\n\nevent: done\ndata: {}\n\n` });
        }
        return route.abort();
      });
      await page.goto(process.env.CHAT_TEST_ORIGIN || 'http://127.0.0.1:8061');
      await page.getByRole('button', { name: 'Open concierge chat' }).click();
      await page.getByRole('button', { name: 'Send message' }).waitFor();
      await page.waitForFunction(() => !document.querySelector('#send').disabled);
      assert.equal(await page.locator('#reset').isDisabled(), true);
      await page.getByLabel('Your message', { exact: true }).fill('<img src=x onerror=alert(1)> Hello from my browser.');
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.getByText('Reply saved.', { exact: false }).waitFor();
      assert.equal(await page.locator('#reset').isEnabled(), true);
      assert.equal(await page.locator('#chat-log img').count(), 0);
      await page.reload();
      await page.waitForFunction(() => !document.querySelector('#send').disabled);
      await page.getByRole('button', { name: 'Open concierge chat' }).click();
      assert.equal(await page.locator('.chat-message').count(), 2);
      assert.equal(await page.locator('#reset').isEnabled(), true);
      // Use ordinary guest copy for the review screenshots.
      turns[0].question = 'Hello, I would like to try the conversation.';
      // "Reload chat" appears only after an error, so reload the page instead.
      assert.equal(await page.getByRole('button', { name: 'Reload chat' }).isVisible(), false);
      await page.reload();
      await page.waitForFunction(() => !document.querySelector('#send').disabled);
      await page.getByRole('button', { name: 'Open concierge chat' }).click();
      await page.waitForFunction(() => document.querySelector('#chat-log').textContent.includes('Hello, I would like'));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `.local/screenshots/sin-61-${name}.png`, fullPage: true });
      await page.getByRole('button', { name: 'New conversation' }).click();
      await page.getByText('New conversation ready.', { exact: false }).waitFor();
      assert.equal(await page.locator('.chat-message').count(), 0);
      assert.equal(await page.locator('#reset').isDisabled(), true);
      mode = 'hold';
      await page.getByLabel('Your message', { exact: true }).fill('Stop this reply');
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.getByRole('button', { name: 'Stop reply' }).click();
      await page.getByText('Reply stopped.', { exact: false }).waitFor();
      assert.equal(await page.locator('.chat-message').count(), 0);
      assert.equal(await page.locator('#reset').isDisabled(), true);
      assert.equal(await page.locator('#send').isEnabled(), true);
      mode = 'fail';
      await page.getByLabel('Your message', { exact: true }).fill('This reply will fail');
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.getByText('Demo reply failed. Try again.', { exact: true }).waitFor();
      assert.equal(await page.locator('.chat-message').count(), 0);
      assert.equal(await page.locator('#reset').isDisabled(), true);
      assert.equal(await page.locator('#send').isEnabled(), true);
      mode = 'complete';
      await page.getByLabel('Your message', { exact: true }).fill('Continue after failure');
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.getByText('Reply saved.', { exact: false }).waitFor();
      assert.equal(await page.locator('.chat-message').count(), 2);
      assert.deepEqual(errors, []);
      console.log(`${name}: send, safe text, refresh, reset, stop, failure/retry, overflow and console checks passed`);
      await context.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
