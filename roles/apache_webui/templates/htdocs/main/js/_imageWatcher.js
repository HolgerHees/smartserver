mx.ImageWatcher = (function( ret ) {
    function refreshImage(container)
    {
        var image = container.querySelector('img');
        var timeSpan = container.querySelector('span.time');
        var nameSpan = container.querySelector('span.name');

        var datetime = new Date();
        var h = datetime.getHours();
        var m = datetime.getMinutes();
        var s = datetime.getSeconds();

        var time = ("0" + h).slice(-2) + ':' + ("0" + m).slice(-2) + ':' + ("0" + s).slice(-2);
        timeSpan.innerText = time;
        nameSpan.innerText = image.getAttribute('data-name');

        let id = Date.now();
        let src = image.getAttribute('data-src') + '?' + id;

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
                mx.Timer.register(function(){refreshImage(container);},image.getAttribute('data-interval'));
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

            var timeSpan = document.createElement("span");
            timeSpan.classList.add("time");

            var nameSpan = document.createElement("span");
            nameSpan.classList.add("name");

            container.appendChild(timeSpan);
            container.appendChild(nameSpan);

            refreshImage(container);
        });
    };

    return ret;
})( mx.ImageWatcher || {} ); 
