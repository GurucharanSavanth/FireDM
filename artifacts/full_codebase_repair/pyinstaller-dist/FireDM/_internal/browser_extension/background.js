const NATIVE_HOST = 'com.firedm.nativehost';

async function sendToNative(msg) {
  const nonce = crypto.randomUUID();
  const origin = chrome.runtime.getURL('');
  const challenge = await chrome.runtime.sendNativeMessage(NATIVE_HOST, {
    action: 'challenge',
    origin: origin,
    nonce: nonce
  });

  return chrome.runtime.sendNativeMessage(NATIVE_HOST, {
    ...msg,
    origin: origin,
    nonce: nonce,
    signature: challenge.signature
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'download') {
    sendToNative(request).then(sendResponse);
    return true;
  }
  if (request.action === 'capture_stream') {
    sendToNative(request).then(sendResponse);
    return true;
  }
});
