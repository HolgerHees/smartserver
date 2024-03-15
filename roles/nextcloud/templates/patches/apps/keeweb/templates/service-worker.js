const VERSION = '1.12.3';

self.addEventListener('install', event =>
    event.waitUntil(
        caches.open('v1').then(cache =>
            fetch('.?v=' + VERSION).then(response => {
                if (response.ok) {
                    return cache.put('.', response);
                }
            })
        )
    )
);

self.addEventListener('fetch', event => {
    if( event.request.url.indexOf("keeweb?config") == -1 )
    {   
        event.respondWith(
            fetch(event.request)
        );
    }
    else
    {
        event.respondWith(
            caches.match(event.request.url).then(response => response || fetch(event.request))
        );
    }
});
