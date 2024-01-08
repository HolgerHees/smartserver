mx.ImageWatcher = (function( ret ) {
    var activeAnimations = {};
    var activeTimer = {};

    function getInterval(container)
    {
        return container.getAttribute(container.classList.contains("fullscreen") ? 'data-fullscreen-interval' : 'data-preview-interval')
    }

    function refreshImage(container, last_duration)
    {
        var index = container.getAttribute("data-index");
        activeTimer[index] = null;

        var image = container.querySelector('img');
        var timeSpan = container.querySelector('span.time');

        var datetime = new Date();
        var h = datetime.getHours();
        var m = datetime.getMinutes();
        var s = datetime.getSeconds();

        var interval = getInterval(container);
        var age = ( interval - 200 - last_duration );
        if( age < 0 ) age = 0;

        //console.log(container.offsetHeight,container.offsetWidth);

        let id = Date.now();
        let src = container.getAttribute('data-src') + '?' + id + '&age=' + age;

        if( !container.classList.contains("fullscreen") ) src += "&width=" + container.offsetWidth * 1.5 + "&height=" + container.offsetHeight * 1.5;

        const startTime = performance.now();

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

                const duration = performance.now() - startTime;
                const interval = getInterval(container) - duration;

                if( interval > 0 )
                {
                    activeTimer[index] = mx.Timer.register( function(){refreshImage(container, duration);}, interval );
                }
                else
                {
                    refreshImage(container, duration);
                }
            }
            else
            {
                mx.Page.handleRequestError(this.status,src,function(){refreshImage(container, duration);});
            }
        };
        xhr.send();
    }

    ret.init = function(selector)
    {
        var containers = mx.$$(selector);
        containers.forEach(function(container, index){
            container.setAttribute("data-index", index);
            activeTimer[index] = null;
            activeAnimations[index] = null;

            container.addEventListener("click",function(event)
            {
                event.stopPropagation();

                var index = container.getAttribute("data-index");

                if( container.classList.contains("fullscreen") )
                {
                    if( activeAnimations[index] == null ) return;

                    var data = activeAnimations[index];
                    container.style.left = data["offsets"]["left"] + "px";
                    container.style.top = data["offsets"]["top"] + "px";
                    container.style.width = data["width"] + "px";
                    container.style.height = data["height"] + "px";

                    // force refresh
                    container.offsetHeight;

                    window.setTimeout( function()
                    {
                        if( activeAnimations[index] == null ) return;

                        container.classList.remove("fullscreen");
                        container.style.transition = "";
                        container.style.left = "";
                        container.style.top = "";
                        container.style.right = "";
                        container.style.bottom = "";
                        container.style.width = "";
                        container.style.height = "";

                        activeAnimations[index]["placeholder"].parentNode.removeChild(activeAnimations[index]["placeholder"]);
                        activeAnimations[index] = null;
                    },300);
                }
                else
                {
                    if( activeAnimations[index] != null ) return;

                    var data = {
                        "offsets":  mx.Core.getOffsets(container),
                        "width": container.offsetWidth,
                        "height": container.offsetHeight,
                        "placeholder": document.createElement("div")
                    }
                    activeAnimations[index] = data;

                    //console.log(animationOffsets,animationWidth, animationHeight);

                    data["placeholder"].classList.add("placeholder");
                    data["placeholder"].style.width = data["width"] + "px";
                    data["placeholder"].style.height = data["height"] + "px";
                    container.parentNode.insertBefore(data["placeholder"], container);
                    container.style.left = data["offsets"]["left"] + "px";
                    container.style.top = data["offsets"]["top"] + "px";
                    container.style.width = data["width"] + "px";
                    container.style.height = data["height"] + "px";

                    // force refresh
                    container.offsetHeight;

                    container.classList.add("fullscreen");
                    container.style.transition = "all 0.3s";
                    container.style.left = "0";
                    container.style.top = "0";
                    container.style.right = "0";
                    container.style.bottom = "0";
                    container.style.width = "100%";
                    container.style.height = "100%";
                }

                if( activeTimer[index] != null )
                {
                    mx.Timer.stop(activeTimer[index]);
                    refreshImage(container, 0);
                }
            });

            var timeSpan = document.createElement("span");
            timeSpan.classList.add("time");
            container.appendChild(timeSpan);

            var nameSpan = document.createElement("span");
            nameSpan.classList.add("name");
            nameSpan.innerText = container.getAttribute('data-name');
            container.appendChild(nameSpan);

            var gallerySpan = document.createElement("span");
            gallerySpan.classList.add("gallery");
            gallerySpan.classList.add("icon-chart-area");
            container.appendChild(gallerySpan);
            gallerySpan.addEventListener("click",function(event)
            {
                event.stopPropagation();
                mx.Actions.openEntryById(event,container.getAttribute('data-internal-menu'));
            });

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

            refreshImage(container, 0);
        });
    };

    return ret;
})( mx.ImageWatcher || {} ); 
