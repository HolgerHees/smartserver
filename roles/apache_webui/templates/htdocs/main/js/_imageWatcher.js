mx.ImageWatcher = (function( ret ) {
    function getInterval(container)
    {
        return container.getAttribute(container.classList.contains("fullscreen") ? 'data-fullscreen-interval' : 'data-preview-interval')
    }

    function refreshImage(container, interval)
    {
        var image = container.querySelector('img');
        var timeSpan = container.querySelector('span.time');

        var datetime = new Date();
        var h = datetime.getHours();
        var m = datetime.getMinutes();
        var s = datetime.getSeconds();

        var interval = getInterval(container);

        let id = Date.now();
        let src = container.getAttribute('data-src') + '?' + id + '&age=' + ( interval - 100 );

        var xhr = new XMLHttpRequest();
        xhr.open("GET", src);
        xhr.withCredentials = true;
        xhr.responseType = 'blob';
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                var imageURL = window.URL.createObjectURL(this.response);
                image.setAttribute('src', imageURL );

                var time = ("0" + h).slice(-2) + ':' + ("0" + m).slice(-2) + ':' + ("0" + s).slice(-2);
                timeSpan.innerText = time;

                mx.Timer.register(function(){refreshImage(container);}, getInterval(container) );
            }
            else
            {
                mx.Page.handleRequestError(this.status,src,function(){refreshImage(container);});
            }
        };
        xhr.send();
    }

    ret.init = function(selector)
    {
        var containers = mx.$$(selector);
        containers.forEach(function(container){

            container.addEventListener("click",function(event)
            {
                event.stopPropagation();
                container.classList.toggle("fullscreen");
            });

            var timeSpan = document.createElement("span");
            timeSpan.classList.add("time");
            container.appendChild(timeSpan);

            var nameSpan = document.createElement("span");
            nameSpan.classList.add("name");
            nameSpan.innerText = container.getAttribute('data-name');
            container.appendChild(nameSpan);

            if( container.getAttribute('data-internal-menu') )
            {
                var gallerySpan = document.createElement("span");
                gallerySpan.classList.add("gallery");
                gallerySpan.classList.add("icon-chart-area");
                container.appendChild(gallerySpan);
                gallerySpan.addEventListener("click",function(event)
                {
                    event.stopPropagation();
                    mx.Actions.openEntryById(event,container.getAttribute('data-internal-menu'));
                });
            }

            var externalSpan = document.createElement("span");
            externalSpan.classList.add("external");
            externalSpan.classList.add("icon-export");
            container.appendChild(externalSpan);
            externalSpan.addEventListener("click",function(event)
            {
                event.stopPropagation();

                var win = window.open(container.getAttribute('data-external-url'), '_blank');
                win.focus();
            });

            //mx.Actions.openEntryById(event,\'automation-cameras-{{camera['ftp_upload_name']}}\')

            refreshImage(container);
        });
    };

    return ret;
})( mx.ImageWatcher || {} ); 
