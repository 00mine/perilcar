// PerilCar Service Worker — cache offline per inventario mobile
const CACHE = 'perilcar-v1';
const CACHE_URLS = [
  '/inventario-mobile',
  '/static/js/autocomplete.js',
  'https://cdn.socket.io/4.7.5/socket.io.min.js',
];

// Installa: metti in cache le risorse essenziali
self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(CACHE).then(function(c){
      return Promise.allSettled(CACHE_URLS.map(url => c.add(url).catch(()=>{})));
    }).then(function(){ return self.skipWaiting(); })
  );
});

// Attiva: pulisci cache vecchie
self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)));
    }).then(function(){ return self.clients.claim(); })
  );
});

// Fetch: network first, poi cache
self.addEventListener('fetch', function(e){
  // Ignora richieste non GET e API (quelle vanno sempre al server o alla coda)
  if(e.request.method !== 'GET') return;
  var url = new URL(e.request.url);
  if(url.pathname.startsWith('/api/')) return;
  if(url.pathname.startsWith('/socket.io')) return;

  e.respondWith(
    fetch(e.request).then(function(res){
      // Aggiorna cache con risposta fresca
      if(res.ok){
        var clone = res.clone();
        caches.open(CACHE).then(function(c){ c.put(e.request, clone); });
      }
      return res;
    }).catch(function(){
      // Offline: servi dalla cache
      return caches.match(e.request).then(function(cached){
        return cached || new Response('Offline - risorsa non disponibile', {status:503});
      });
    })
  );
});
