// FireDM popup — drives bridge status, capture action, dispatch log.

const NATIVE_HOST = 'com.firedm.nativehost';
const LOG_KEY = 'firedm_recent_dispatches';
const LOG_MAX = 5;

const els = {
  bridge: document.getElementById('bridge'),
  dot:    document.getElementById('dot'),
  gauge:  document.getElementById('gauge'),
  log:    document.getElementById('log'),
  btn:    document.getElementById('capture'),
};

// ---------- Bridge probe ----------
function pingBridge() {
  // sendNativeMessage will reject if the host isn't installed; use a noop ping.
  try {
    chrome.runtime.sendNativeMessage(
      NATIVE_HOST,
      { action: 'ping', origin: chrome.runtime.getURL(''), nonce: '0', signature: '' },
      () => {
        const err = chrome.runtime.lastError;
        if (err) return setBridge(false, err.message || 'unreachable');
        setBridge(true, 'linked');
      }
    );
  } catch (_e) {
    setBridge(false, 'unsupported');
  }
}

function setBridge(linked, label) {
  if (linked) {
    els.bridge.innerHTML = `<span class="dot" id="dot"></span>LINKED`;
    els.bridge.className = 'val val--hot';
    els.gauge.classList.remove('gauge--cold');
  } else {
    els.bridge.innerHTML = `<span class="dot dot--cold" id="dot"></span>${(label || 'OFFLINE').toUpperCase()}`;
    els.bridge.className = 'val val--cool';
    els.gauge.classList.add('gauge--cold');
  }
}

// ---------- Capture action ----------
els.btn.addEventListener('click', () => {
  els.btn.disabled = true;
  const original = els.btn.firstChild.textContent;
  els.btn.firstChild.textContent = 'INTERROGATING…';

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs && tabs[0];
    if (!tab) {
      restoreBtn(original);
      return;
    }
    chrome.tabs.sendMessage(tab.id, { action: 'capture' }, (_resp) => {
      // Read back recent dispatches even if the content script didn't respond
      // (capture happens via background → native host pipeline).
      pushDispatch({
        name: shortName(tab.url || tab.title || 'unknown'),
        bytes: '—',
      });
      restoreBtn(original);
    });
  });
});

function restoreBtn(label) {
  els.btn.disabled = false;
  els.btn.firstChild.textContent = label;
}

// ---------- Dispatch log ----------
function loadDispatches() {
  return new Promise((resolve) => {
    chrome.storage?.local?.get?.([LOG_KEY], (data) => {
      resolve(Array.isArray(data?.[LOG_KEY]) ? data[LOG_KEY] : []);
    }) ?? resolve([]);
  });
}

function saveDispatches(list) {
  try { chrome.storage?.local?.set?.({ [LOG_KEY]: list }); } catch (_e) {}
}

function pushDispatch(entry) {
  loadDispatches().then((list) => {
    const next = [{ id: hexId(), name: entry.name, bytes: entry.bytes || '—', t: Date.now() }, ...list].slice(0, LOG_MAX);
    saveDispatches(next);
    renderLog(next);
  });
}

function renderLog(list) {
  if (!list.length) {
    els.log.innerHTML = `<li class="log__empty">— no dispatches yet —</li>`;
    return;
  }
  els.log.innerHTML = list.map((it) => `
    <li class="log__item">
      <span class="log__id">0x${it.id}</span>
      <span class="log__name" title="${escapeHTML(it.name)}">${escapeHTML(it.name)}</span>
      <span class="log__bytes">${escapeHTML(it.bytes)}</span>
    </li>
  `).join('');
}

// ---------- Helpers ----------
function hexId() {
  const buf = new Uint8Array(2);
  (crypto || window.crypto).getRandomValues(buf);
  return Array.from(buf).map((b) => b.toString(16).padStart(2, '0')).join('').toUpperCase();
}

function shortName(s) {
  try {
    const u = new URL(s);
    const tail = u.pathname.split('/').filter(Boolean).pop() || u.hostname;
    return tail.length > 28 ? tail.slice(0, 25) + '…' : tail;
  } catch (_e) {
    return String(s).slice(0, 28);
  }
}

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

// ---------- Init ----------
pingBridge();
loadDispatches().then(renderLog);
