// jianyu service worker —— v3.7.19 改为"立即自销毁"
// 原因：之前 network-first 缓存导致用户浏览器加载旧 index.html，
//       即使 GitHub Pages 部署了新版也看不到。
// 修法：激活时清理所有旧 cacheStorage + 注销自身 → 永远走网络。
const KILL_CACHE = 'jianyu-sw-kill-2026.08.06.1508';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
      .then(() => self.registration.unregister())
      .then(() => self.clients.matchAll({ includeUncontrolled: true }))
      .then((clients) => clients.forEach((c) => c.navigate(c.url)))
  );
});

self.addEventListener('fetch', (event) => {
  // 透传到网络（不再缓存任何东西）
  event.respondWith(fetch(event.request));
});
