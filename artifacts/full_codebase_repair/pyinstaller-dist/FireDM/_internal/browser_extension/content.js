// FireDM content script — captures media URLs and forwards to background.
function captureMedia() {
  const links = document.querySelectorAll('a[href], video[src], source[src]');
  links.forEach(el => {
    const url = el.href || el.src;
    if (!url) return;
    if (/\.(mp4|mkv|webm|mp3|m4a|m3u8|mpd)(\?|$)/i.test(url)) {
      chrome.runtime.sendMessage({
        action: 'capture_stream',
        manifest_url: url,
        page_url: window.location.href
      });
    }
  });
}

document.addEventListener('DOMContentLoaded', captureMedia);
