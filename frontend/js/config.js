// config.js — all constants in one place
const CONFIG = {
  wsProtocol : location.protocol === 'https:' ? 'wss:' : 'ws:',
  wsHost     : (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
                 ? 'localhost:8000'
                 : location.host,
  maxReconnects   : 5,
  maxAudioBytes   : 10 * 1024 * 1024,   // 10MB
  userIdKey       : 'rafeeq_uid',
};

CONFIG.wsBase = `${CONFIG.wsProtocol}//${CONFIG.wsHost}`;