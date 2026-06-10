// socket.js
const Socket = (() => {
  let ws;
  let reconnectAttempts = 0;
  const userId = Identity.getUserId();

  function connect() {
    ws = new WebSocket(`${CONFIG.wsBase}/ws/${userId}`);
    UI.setMicEnabled(false);

    ws.onopen = () => {
      reconnectAttempts = 0;
      UI.setIdle();
      UI.setStatus('اضغط مع الاستمرار للتحدث');
    };

    ws.onclose = () => {
      UI.setMicEnabled(false);
      if (reconnectAttempts < CONFIG.maxReconnects) {
        reconnectAttempts++;
        const wait = reconnectAttempts * 2;
        UI.setStatus(`جاري إعادة الاتصال... (${reconnectAttempts}/${CONFIG.maxReconnects})`);
        setTimeout(connect, wait * 1000);
      } else {
        UI.setStatus('تعذر الاتصال — أعد تحميل الصفحة');
      }
    };

    ws.onerror = () => {
      UI.setStatus('خطأ في الاتصال...');
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        const msg = JSON.parse(event.data);

        if (msg.type === 'transcript') {
          UI.addUserBubble(msg.text);
          UI.setThinking();                         // ← show thinking dots
          UI.setStatus('رفيق يفكر...');

        } else if (msg.type === 'reply_chunk') {
          if (msg.text) {
            UI.setSpeaking();                       // ← first chunk: switch to speaking
            UI.appendRafeeqChunk(msg.text);
          }
          if (msg.is_last) {
            UI.setStatus('اضغط مع الاستمرار للتحدث');
          } else {
            UI.setStatus('رفيق يتحدث...');
          }

        } else if (msg.type === 'error') {
          UI.setIdle();
          UI.setStatus(msg.message);
        }

      } else {
        // audio bytes
        const blob = new Blob([event.data], { type: 'audio/wav' });
        Audio_.enqueue(blob);
      }
    };
  }

  function send(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(data);
    }
  }

  function isOpen() {
    return ws && ws.readyState === WebSocket.OPEN;
  }

  return { connect, send, isOpen };
})();