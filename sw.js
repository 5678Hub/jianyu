// GB2762 Cache Buster Service Worker
// 拦截所有 fetch 请求,绕过浏览器 disk cache,强制从服务器拉最新

const CACHE_BUST = 'v74-food-root-node-2026-08-29-21:40';

self.addEventListener('install', (event) => {
  // 立即激活,不等旧 SW 关闭
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // v45: 激进清理所有旧缓存名 + 立即接管页面
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  // 只拦截 GET 请求,POST/PUT 等不动
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // 拦截同源 / 跨源请求:加 cache-bust query + 强制 reload
  // 注意:不能修改 req.url 给原页面用(SW 只能传递,但 fetch 重写允许)
  event.respondWith(
    fetch(req.url + (req.url.includes('?') ? '&' : '?') + 'sw_bust=' + Date.now(), {
      cache: 'reload',  // 强制浏览器从服务器拉,绕开 disk cache
      headers: req.headers,
    }).catch((err) => {
      // 网络失败:降级不报错,让浏览器走原请求
      return fetch(req, { cache: 'reload' });
    })
  );
});

self.addEventListener('message', (event) => {
  // 页面可发送 SKIP_WAITING 立即激活新 SW
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
