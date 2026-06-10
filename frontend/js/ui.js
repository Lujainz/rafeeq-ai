const UI = (() => {

  const micBtn    = document.getElementById('mic-btn');
  const micWrap   = document.getElementById('mic-wrap');
  const statusEl  = document.getElementById('status');
  const bubblesEl = document.getElementById('bubbles');
  const waveform  = document.getElementById('waveform');

  // ── Empty state ────────────────────────────────────────────
  const emptyState = document.createElement('div');
  emptyState.className = 'chat-empty';
  emptyState.dir = 'rtl';
  emptyState.innerHTML = `
    <p>
      مرحباً! أنا رفيق، مساعدك الصوتي<br/>
      اضغط على الميكروفون لبدء المحادثة
    </p>
  `;
  bubblesEl.appendChild(emptyState);

  // ── Thinking bubble ────────────────────────────────────────
  const thinkingBubble = document.createElement('div');
  thinkingBubble.className = 'thinking-bubble';
  thinkingBubble.innerHTML = `
    <span class="thinking-dot"></span>
    <span class="thinking-dot"></span>
    <span class="thinking-dot"></span>
  `;

  let currentRafeeqBubble = null;
  let hasMessages = false;

  // ── Status ─────────────────────────────────────────────────
  function setStatus(text) {
    statusEl.textContent = text;
  }

  function setMicEnabled(enabled) {
    micBtn.disabled = !enabled;
  }

  // ── Mic states ─────────────────────────────────────────────
  function _clearStates() {
    micWrap.classList.remove('recording', 'thinking', 'speaking');
    waveform.classList.remove('active');
  }

  function setIdle() {
    _clearStates();
    setMicEnabled(true);
  }

  function setRecording() {
    _clearStates();
    micWrap.classList.add('recording');
  }

  function setThinking() {
    _clearStates();
    micWrap.classList.add('thinking');
    setMicEnabled(false);
    _showThinking();
  }

  function setSpeaking() {
    _clearStates();
    micWrap.classList.add('speaking');
    waveform.classList.add('active');
    _hideThinking();
    setMicEnabled(true);
  }

  function setMicRecording(active) {
    if (active) setRecording(); else setIdle();
  }

  // ── Thinking bubble ────────────────────────────────────────
  function _showThinking() {
    if (!thinkingBubble.parentNode) {
      bubblesEl.appendChild(thinkingBubble);
    }
    thinkingBubble.classList.add('visible');
    thinkingBubble.scrollIntoView({ behavior: 'smooth' });
  }

  function _hideThinking() {
    thinkingBubble.classList.remove('visible');
    if (thinkingBubble.parentNode) {
      bubblesEl.removeChild(thinkingBubble);
    }
  }

  // ── Remove empty state on first message ───────────────────
  function _removeEmptyState() {
    if (!hasMessages && emptyState.parentNode) {
      bubblesEl.removeChild(emptyState);
      hasMessages = true;
    }
  }

  // ── Time helper ────────────────────────────────────────────
  function _now() {
    return new Date().toLocaleTimeString('ar-SA', {
      hour: '2-digit', minute: '2-digit', hour12: true
    });
  }

  // ── Bubbles ────────────────────────────────────────────────
  function addUserBubble(text) {
    _removeEmptyState();
    currentRafeeqBubble = null;
    _hideThinking();
    const div = document.createElement('div');
    div.className = 'bubble user';
    div.dir = 'rtl';
    div.innerHTML = `${text}<span class="bubble-time">${_now()}</span>`;
    bubblesEl.appendChild(div);
    div.scrollIntoView({ behavior: 'smooth' });
  }

  function appendRafeeqChunk(text) {
    _removeEmptyState();
    if (currentRafeeqBubble) {
      const timeEl = currentRafeeqBubble.querySelector('.bubble-time');
      if (timeEl) {
        timeEl.insertAdjacentText('beforebegin', ' ' + text);
      } else {
        currentRafeeqBubble.textContent += ' ' + text;
      }
    } else {
      const div = document.createElement('div');
      div.className = 'bubble rafeeq';
      div.dir = 'rtl';
      div.innerHTML = `${text}<span class="bubble-time">${_now()}</span>`;
      bubblesEl.appendChild(div);
      currentRafeeqBubble = div;
    }
    currentRafeeqBubble.scrollIntoView({ behavior: 'smooth' });
  }

  function resetRafeeqBubble() {
    currentRafeeqBubble = null;
  }

  return {
    micBtn,
    setStatus,
    setMicEnabled,
    setMicRecording,
    setIdle,
    setRecording,
    setThinking,
    setSpeaking,
    addUserBubble,
    appendRafeeqChunk,
    resetRafeeqBubble,
  };
})();