// identity.js — stable user ID that persists across refreshes
const Identity = (() => {
  function getUserId() {
    let id = localStorage.getItem(CONFIG.userIdKey);
    if (!id) {
      id = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem(CONFIG.userIdKey, id);
    }
    return id;
  }

  return { getUserId };
})();