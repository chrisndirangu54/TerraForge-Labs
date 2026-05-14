self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('.pmtiles')) {
    event.respondWith(fetch(event.request));
  }
});
