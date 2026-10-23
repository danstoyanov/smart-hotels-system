// SSE frames may cross network chunks, including within UTF-8 characters.
export async function readEvents(stream, onEvent) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  function drain() {
    let end;
    while ((end = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      const lines = frame.split('\n');
      const name = lines.find(line => line.startsWith('event: '))?.slice(7);
      const data = lines.filter(line => line.startsWith('data: ')).map(line => line.slice(6)).join('\n');
      if (name && data) onEvent(name, JSON.parse(data));
    }
  }
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      if (buffer.length > 200000) throw new Error('Reply too large. Reload chat.');
      drain();
    }
    buffer += decoder.decode();
    drain();
    if (buffer.trim()) throw new Error('Incomplete reply. Reload chat before sending again.');
  } finally {
    reader.releaseLock();
  }
}

