// audio.js — recording and playback, completely separate from UI and socket
const Audio_ = (() => {
  let mediaRecorder, audioChunks, stream;

  // ── Playback queue (promise chain) ──────────────────────────
  let playbackChain = Promise.resolve();

  function enqueue(blob) {
    playbackChain = playbackChain.then(() => _play(blob));
  }

  function _play(blob) {
    return new Promise((resolve) => {
      const url = URL.createObjectURL(blob);
      const audio = new window.Audio(url);
      audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
      audio.onerror = () => { URL.revokeObjectURL(url); resolve(); };
      audio.play().catch(() => { URL.revokeObjectURL(url); resolve(); });
    });
  }

  function resetQueue() {
    playbackChain = Promise.resolve();
  }

  // ── Recording ────────────────────────────────────────────────
  async function startRecording(onStop) {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      UI.setStatus('يرجى السماح بالوصول إلى الميكروفون');
      return;
    }

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';

    mediaRecorder = new MediaRecorder(stream, { mimeType });
    audioChunks   = [];

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      stream.getTracks().forEach(t => t.stop());
      onStop(blob);   // hand the blob back to whoever called startRecording
    };

    mediaRecorder.start();
    UI.setMicRecording(true);
    UI.setStatus('🎤 جاري الاستماع...');
  }

  function stopRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') return;
    mediaRecorder.stop();
    UI.setMicRecording(false);
    UI.setStatus('جاري الإرسال...');
  }

  return {
    enqueue,
    resetQueue,
    startRecording,
    stopRecording,
  };
})();