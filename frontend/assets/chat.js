import { readEvents } from './sse.js';

const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const send = document.querySelector('#send');
const stop = document.querySelector('#stop');
const reset = document.querySelector('#reset');
const retry = document.querySelector('#retry-chat');
const log = document.querySelector('#chat-log');
const status = document.querySelector('#chat-status');
let controller;
let ready = false;

function controls(busy) {
  send.disabled = busy || !ready;
  input.disabled = busy || !ready;
  reset.disabled = busy || !ready;
  retry.disabled = busy;
  stop.hidden = !busy;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    cache: 'no-store', signal: AbortSignal.timeout(10000), ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!response.ok) {
    if (response.status === 401) {
      ready = false;
      throw new Error('Your session expired. Choose Reload chat to start a new session.');
    }
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Chat unavailable. Try again shortly.');
  }
  return response;
}

function message(label, text, sources = []) {
  const item = document.createElement('div');
  item.className = 'chat-message';
  const name = document.createElement('strong');
  name.textContent = label;
  const body = document.createElement('p');
  body.textContent = text;
  item.append(name, body);
  if (sources.length) {
    const links = document.createElement('ul');
    links.setAttribute('aria-label', 'Hotel information read');
    for (const source of sources) {
      // Only local, versioned hotel records become links. Model text stays plain text.
      if (typeof source.url !== 'string'
          || !/^\/api\/hotel\/(rooms|amenities|policies)\/[a-z0-9-]+\?source_id=[a-z0-9-]+&version=[1-9][0-9]*$/.test(source.url)) continue;
      const row = document.createElement('li');
      const link = document.createElement('a');
      link.href = source.url;
      link.textContent = `${source.title} · demo source v${source.version}`;
      link.target = '_blank';
      link.rel = 'noopener';
      row.append(link);
      links.append(row);
    }
    item.append(links);
  }
  log.append(item);
  return body;
}

async function history() {
  const data = await (await api('/api/history')).json();
  log.replaceChildren();
  for (const turn of data.turns) {
    message('You', turn.question);
    message('Demo assistant', turn.answer, turn.sources || []);
  }
  document.querySelector('#chat-empty').hidden = data.turns.length > 0;
}

async function initialize() {
  controls(true);
  status.textContent = 'Loading your conversation…';
  try {
    await api('/api/session', { method: 'POST' });
    await history();
    ready = true;
    const site = await (await api('/api/site')).json();
    status.textContent = site.assistant_mode === 'vertex'
      ? 'Chat ready. Ask about rooms, amenities or policies. Replies use AI and may contain mistakes.'
      : 'Chat ready. Local stub mode is active; AI answers are not enabled.';
  } catch (error) {
    ready = false;
    status.textContent = error.message;
  } finally {
    controls(false);
  }
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || controller || !ready) return;
  controller = new AbortController();
  controls(true);
  document.querySelector('#chat-empty').hidden = true;
  message('You · sending', question);
  const answer = message('Demo assistant · provisional', '');
  status.textContent = 'Checking hotel information…';
  let result = false;
  let done = false;
  try {
    const response = await api('/api/chat', {
      method: 'POST', signal: controller.signal,
      body: JSON.stringify({ turn_id: crypto.randomUUID(), message: question }),
    });
    await readEvents(response.body, (name, data) => {
      if (name === 'text') answer.textContent += data.text;
      if (name === 'result') { answer.textContent = data.answer; result = true; }
      if (name === 'done') done = true;
      if (name === 'error') throw new Error(data.message);
    });
    if (!result || !done) throw new Error('Reply interrupted. Reload chat before sending again.');
    input.value = '';
    await history();
    status.textContent = 'Reply saved. You can continue or start a new conversation.';
  } catch (error) {
    // Remove provisional output. A committed answer may still be recovered from history.
    try { await history(); } catch { ready = false; }
    status.textContent = error.name === 'AbortError'
      ? 'Reply stopped. Saved history restored. You can try again shortly.' : error.message;
  } finally {
    controller = undefined;
    controls(false);
    if (ready) input.focus();
  }
});

stop.addEventListener('click', () => controller?.abort());
retry.addEventListener('click', initialize);
reset.addEventListener('click', async () => {
  controls(true);
  try {
    await api('/api/conversation', { method: 'POST' });
    await history();
    status.textContent = 'New conversation ready. Earlier messages are no longer shown.';
  } catch (error) {
    status.textContent = error.message;
  } finally {
    controls(false);
  }
});
initialize();
