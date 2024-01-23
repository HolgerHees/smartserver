mx.ImageWatcher = (function( ret ) {
    var activeWatcher = {};

    function getInterval(container)
    {
        return container.getAttribute(container.classList.contains("fullscreen") ? 'data-fullscreen-interval' : 'data-preview-interval')
    }

    function refreshImage(container, last_duration, i18n_component)
    {
        var uid = container.getAttribute("data-uid");
        activeWatcher[uid]["timer"] = null;

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
        //console.log(src);

        const startTime = performance.now();

        var xhr = new XMLHttpRequest();
        xhr.open("GET", src);
        xhr.withCredentials = true;
        xhr.responseType = 'blob';
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            var infoSpan = container.querySelector('span.info');

            if( this.status == 200 )
            {
                var imageURL = window.URL.createObjectURL(this.response);
                image.onload = function()
                {
                    showImage(uid, image, infoSpan);
                }
                image.onerror = function(event)
                {
                    //image.onload = null;
                    //image.onerror = null;
                    //image.setAttribute('src', "/main/img/loading.png" );
                    showError(uid, image, infoSpan, mx.I18N.get("Image error",i18n_component) );
                }
                image.setAttribute('src', imageURL );

                var time = ("0" + h).slice(-2) + ':' + ("0" + m).slice(-2) + ':' + ("0" + s).slice(-2);
                timeSpan.innerText = time;

                const duration = performance.now() - startTime;
                const interval = getInterval(container) - duration;

                if( interval > 0 )
                {
                    activeWatcher[uid]["timer"] = mx.Timer.register( function(){refreshImage(container, duration, i18n_component);}, interval );
                }
                else
                {
                    refreshImage(container, duration, i18n_component);
                }
            }
            else
            {
                showError(uid, image, infoSpan,  this.status == 0 ? mx.I18N.get("Offline",i18n_component) : mx.I18N.get("Error",i18n_component) + ": " + this.status );

                mx.Page.handleRequestError(this.status,src,function(){refreshImage(container, 0, i18n_component);});
            }
        };
        xhr.send();
    }

    function showImage(uid, image, infoSpan)
    {
        infoSpan.style.opacity = "0";
        image.style.visibility = "visible";
        image.style.aspectRatio = "";

        var aspectRation = Math.round( ( image.naturalWidth / image.naturalHeight ) * 100 ) / 100;
        if( aspectRation != activeWatcher[uid]["aspectRatio"] )
        {
            activeWatcher[uid]["aspectRatio"] = aspectRation;
            localStorage.setItem("gallery_aspect_ratio_" + uid, aspectRation);
        }
    }

    function showError(uid, image, infoSpan, errorMsg)
    {
        infoSpan.classList.add("error");
        infoSpan.innerText = errorMsg;
        infoSpan.style.opacity = "1";
        image.style.visibility = "";
        if( activeWatcher[uid]["aspectRatio"] ) image.style.aspectRatio = activeWatcher[uid]["aspectRatio"];
    }

    ret.init = function(selector)
    {
        var containers = mx.$$(selector);
        containers.forEach(function(container, index){
            uid = selector + ":" + index;
            container.setAttribute("data-uid", uid);

            activeWatcher[uid] = {"timer": null, "animation": null, "aspectRatio": null};

            var image = container.querySelector('img');

            var aspectRatio = localStorage.getItem("gallery_aspect_ratio_" + uid);
            if( !aspectRatio ) aspectRatio = 1.78;
            activeWatcher[uid]["aspectRatio"] = aspectRatio;
            image.style.aspectRatio = aspectRatio;
        });
    }

    ret.post = function(selector, i18n_component)
    {
        var containers = mx.$$(selector);
        containers.forEach(function(container){
            var uid = container.getAttribute("data-uid");

            container.addEventListener("click",function(event)
            {
                event.stopPropagation();

                var uid = container.getAttribute("data-uid");

                if( container.classList.contains("fullscreen") )
                {
                    if( activeWatcher[uid]["animation"] == null ) return;

                    var data = activeWatcher[uid]["animation"];
                    container.style.left = data["offsets"]["left"] + "px";
                    container.style.top = data["offsets"]["top"] + "px";
                    container.style.width = data["width"] + "px";
                    container.style.height = data["height"] + "px";

                    // force refresh
                    container.offsetHeight;

                    window.setTimeout( function()
                    {
                        if( activeWatcher[uid]["animation"] == null ) return;

                        container.classList.remove("fullscreen");
                        container.style.transition = "";
                        container.style.left = "";
                        container.style.top = "";
                        container.style.right = "";
                        container.style.bottom = "";
                        container.style.width = "";
                        container.style.height = "";

                        activeWatcher[uid]["animation"]["placeholder"].parentNode.removeChild(activeWatcher[uid]["animation"]["placeholder"]);
                        activeWatcher[uid]["animation"] = null;
                    },300);
                }
                else
                {
                    if( activeWatcher[uid]["animation"] != null ) return;

                    var data = {
                        "offsets":  mx.Core.getOffsets(container),
                        "width": container.offsetWidth,
                        "height": container.offsetHeight,
                        "placeholder": document.createElement("div")
                    }
                    activeWatcher[uid]["animation"] = data;

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

                if( activeWatcher[uid]["timer"] != null )
                {
                    mx.Timer.stop(activeWatcher[uid]["timer"]);
                    refreshImage(container, 0, i18n_component);
                }
            });

            var timeSpan = document.createElement("span");
            timeSpan.classList.add("time");
            container.appendChild(timeSpan);

            var nameSpan = document.createElement("span");
            nameSpan.classList.add("name");
            nameSpan.innerText = container.getAttribute('data-name');
            container.appendChild(nameSpan);

            if( container.hasAttribute('data-internal-menu') )
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

            var infoSpan = document.createElement("span");
            infoSpan.classList.add("info");
            infoSpan.innerText = mx.I18N.get("Loading",i18n_component) + " ...";
            container.appendChild(infoSpan);

            refreshImage(container, 0, i18n_component);
        });
    };

    return ret;
})( mx.ImageWatcher || {} ); 
