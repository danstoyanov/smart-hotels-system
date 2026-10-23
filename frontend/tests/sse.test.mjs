import assert from 'node:assert/strict';
import test from 'node:test';
import { readEvents } from '../assets/sse.js';

function stream(bytes, size) {
  return new ReadableStream({
    start(controller) {
      for (let offset = 0; offset < bytes.length; offset += size) {
        controller.enqueue(bytes.slice(offset, offset + size));
      }
      controller.close();
    },
  });
}

test('SSE handles split frames and multibyte UTF-8', async () => {
  const bytes = new TextEncoder().encode('event: text\ndata: {"text":"Kyiv · Київ"}\n\nevent: done\ndata: {}\n\n');
  for (const size of [1, 3, 17, 1000]) {
    const events = [];
    await readEvents(stream(bytes, size), (name, data) => events.push([name, data]));
    assert.deepEqual(events, [['text', { text: 'Kyiv · Київ' }], ['done', {}]]);
  }
});

test('SSE rejects truncated frames and invalid JSON', async () => {
  for (const body of ['event: done\ndata: {}', 'event: text\ndata: invalid\n\n']) {
    await assert.rejects(readEvents(stream(new TextEncoder().encode(body), 1), () => {}));
  }
});
