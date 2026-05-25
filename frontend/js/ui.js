// ui.js — all DOM updates in one place
const UI = (() => {
  const micBtn  = document.getElementById('mic-btn');
  const status  = document.getElementById('status');
  const bubbles = document.getElementById('bubbles');

  let currentRafeeqBubble = null;

  function setStatus(text) {
    status.textContent = text;
  }

  function setMicEnabled(enabled) {
    micBtn.disabled = !enabled;
  }

  function setMicRecording(active) {
    micBtn.classList.toggle('recording', active);
  }

  function addUserBubble(text) {
    currentRafeeqBubble = null;
    const div = document.createElement('div');
    div.className = 'bubble user';
    div.textContent = text;
    bubbles.appendChild(div);
    div.scrollIntoView({ behavior: 'smooth' });
  }

  function appendRafeeqChunk(text) {
    if (currentRafeeqBubble) {
      currentRafeeqBubble.textContent += ' ' + text;
    } else {
      const div = document.createElement('div');
      div.className = 'bubble rafeeq';
      div.textContent = text;
      bubbles.appendChild(div);
      div.scrollIntoView({ behavior: 'smooth' });
      currentRafeeqBubble = div;
    }
  }

  function resetRafeeqBubble() {
    currentRafeeqBubble = null;
  }

  return {
    micBtn,
    setStatus,
    setMicEnabled,
    setMicRecording,
    addUserBubble,
    appendRafeeqChunk,
    resetRafeeqBubble,
  };
})();