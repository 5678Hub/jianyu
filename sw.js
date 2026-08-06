// jianyu service worker —— 网络优先，离线回退缓存
// ⚠️ DATA_VERSION 由 scripts/rebuild_index.py 自动维护，请勿手改
const DATA_VERSION = '2026.08.06.0953';
const CACHE = `jianyu-cache-${DATA_VERSION}`;

self.addEventListener('install', (event) => {
  // 预缓存 HTML 骨架，保证首屏可离线
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(['/', '/index.html']))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // 数据版本变了，清理所有旧缓存，避免旧数据长期残留
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  // 跳过非同源（GitHub Pages 不会有，但防御一下）
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(event.request)
      .then((res) => {
        // 在线：始终拿最新数据，同时更新缓存（保证自动更新可见）
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(event.request, copy));
        return res;
      })
      .catch(() => caches.match(event.request))
  );
});