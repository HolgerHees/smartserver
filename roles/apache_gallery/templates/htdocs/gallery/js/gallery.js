mx.Gallery = (function( ret ) {
    const ANIMATION_INSTANT = 0;
    const ANIMATION_SMOOTH = 1;
    const ANIMATION_CUSTOM = 2;

    var isFullscreen = false;
    
    var activeItem = null;
    var activeSlot = null;
    var slotTooltipElement = null;

    var imageHeight = 0;
    var imageWidth = 0;
    var folder = null;
    var requestedScrollPosition = null;
    var debug = false;
    
    var slotOverview = null;

    var gallery = null;
    var galleryPreviousButton = null;
    var galleryNextButton = null;
    var galleryStartPlayButton = null;
    var galleryStopPlayButton = null;
  
    var galleryRect = null;

    var containers = [];
    
    var containerObserver = null;
    var visibleContainer = [];
    
    var tabStartPageX = -1;
    var tabStartScrollX = -1;
    var isTabMoving = false;
    var isTabTouch = false;

    var playTimer = null;
    var isPlaying = false;

    var lastScrollPosition = null;

    function getOffset(element)
    {
        var offset = {left:0,top:0,height:element.offsetHeight, width:element.offsetWidth};
        while (element)
        {
            offset.left += element.offsetLeft;
            offset.top += element.offsetTop;
            offset.left -= element.scrollLeft;
            offset.top -= element.scrollTop;
            element = element.offsetParent;
        }
        offset.left -= window.pageXOffset;
        offset.top -= window.pageYOffset;
        
        return offset;
    }

    function positionSlotTooltip()
    {
        if( !slotTooltipElement.dataset.count )
        {
            mx.Tooltip.hide();
        }
        else
        {            
            let text = slotTooltipElement.dataset.formattedtime + "<br>" + slotTooltipElement.dataset.count + " Bilder";
            mx.Tooltip.setText(text);

            var slotOverviewRect = slotOverview.getBoundingClientRect();
            var slotRect = slotTooltipElement.getBoundingClientRect();
            var tooltipRect = mx.Tooltip.getRootElementRect();
            var tooltipArrowRect = mx.Tooltip.getArrowElementRect();
            
            var pos = ( slotRect.left + slotRect.width / 2 - tooltipRect.width / 2 )
            if( pos < 2 )
            {
                pos = 2;
                var center = slotRect.left + slotRect.width / 2;
                arrowLeft = ( center - pos - tooltipArrowRect.width / 2 + 1) + "px";
            }
            else if( pos + tooltipRect.width > slotOverviewRect.width )
            {
                pos = slotOverviewRect.width - 2 - tooltipRect.width;
                var center = slotRect.left + slotRect.width / 2;
                arrowLeft = ( center - pos - tooltipArrowRect.width / 2 + 1) + "px";
            }
            else
            {
                arrowLeft = "calc(50% - " + (tooltipArrowRect.width / 2 - 1) + "px)";
            }
            
            mx.Tooltip.show(pos, 0, arrowLeft);
        }
    }
    
    function setSlotTooltip(element)
    {
        if( element == slotTooltipElement )
        {
            return;
        }
        
        if( slotTooltipElement != null )
        {
            slotTooltipElement.classList.remove("active");
        }
        
        slotTooltipElement = element;
        slotTooltipElement.classList.add("active");
        
        positionSlotTooltip();
    }
    
    function loadImage(element,callback)
    {
        element.dataset.loaded = true;

        var img = element.querySelector("img");

        element.addEventListener("dragstart",function(e){ e.preventDefault(); });
        var img = document.createElement("img");
        img.src = "image.php?sub=" + folder + "&image=" + element.dataset.src;
        if( typeof callback != "undefined" )
        {
            img.onload = function() {
                callback(true);
            };
            img.onerror = function() {
                callback(false);
            };
        }
        element.appendChild(img);
        
        var srcLabel = document.createElement("span");
        srcLabel.innerHTML = element.dataset.src;
        element.appendChild(srcLabel);

        var timeLabel = document.createElement("span");
        timeLabel.innerHTML = element.dataset.formattedtime;
        element.appendChild(timeLabel);
    }

    function scrollTo(options)
    {
        if( options["behavior"] != ANIMATION_CUSTOM || !isFullscreen )
        {
            options["behavior"] = options["behavior"] == ANIMATION_INSTANT ? 'instant' : 'smooth';
            window.scrollTo(options);
        }
        else
        {
            // happens only for fullscreen
            const startPos = window.scrollX;
            const diff = options["left"] - startPos;
            const max = window.innerWidth;
            const duration = Math.abs(diff) * 800 / max;

            let startTime = null;
            let requestId;
            const loop = function (currentTime) {
                if (!startTime) {
                    startTime = currentTime;
                }

                // Elapsed time in miliseconds
                const time = currentTime - startTime;

                const percent = Math.min(time / duration, 1);
                // https://easings.net/de => easeOutQuint
                const animation = function (x) { return 1 - Math.pow(1 - x, 5); };

                window.scrollTo(startPos + diff * animation(percent), 0);

                // Continue moving
                if (time < duration) requestId = window.requestAnimationFrame(loop);
                else window.cancelAnimationFrame(requestId);
            };
            requestId = window.requestAnimationFrame(loop);
        }
    }

    function scrollToActiveItem(item,behavior)
    {
        if( isFullscreen )
        {
            if( Math.round(window.scrollX) != item.offsetLeft )
            {
                if( debug ) console.log("scrollToActiveItem: " + item.dataset.formattedtime);
    
                requestedScrollPosition = { source: window.scrollX, target: item.offsetLeft };

                scrollTo({ left: requestedScrollPosition["target"], behavior: behavior });
            }
        }
        else
        {
            var targetPosition = item.offsetTop - gallery.offsetTop;
            if( Math.round(window.scrollY) != targetPosition )
            {
                if( debug ) console.log("scrollToActiveItem: " + item.dataset.formattedtime);

                requestedScrollPosition = { source: window.scrollY, target: targetPosition };
                scrollTo({ top: requestedScrollPosition["target"], behavior: behavior });
            }
        }
        
        setActiveItem(item);
    }
    
    function setActiveItem(item)
    {
        if( item != activeItem )
        {
            if( debug ) console.log("setActiveItem: " + item.dataset.formattedtime);
            
            if( activeItem == null || activeItem.dataset.timeslot != item.dataset.timeslot )
            {
                if( activeItem != null )
                {
                    var activeSteplineBar = slotOverview.querySelector(".slot[data-timeslot=\"" + activeItem.dataset.timeslot + "\"]");
                    activeSteplineBar.classList.remove("active");
                }
                var steplineBar = slotOverview.querySelector(".slot[data-timeslot=\"" + item.dataset.timeslot + "\"]");
                steplineBar.classList.add("active");
                
                activeSlot = steplineBar;
                setSlotTooltip(activeSlot);
            }

            activeItem = item;
        }
        
        if( isFullscreen )
        {
            galleryStartPlayButton.style.display = activeItem.dataset.index == 0 || isPlaying ? "none" : "";
            galleryPreviousButton.style.display = activeItem.dataset.index == 0 ? "none" : "";
            galleryNextButton.style.display = activeItem.dataset.index == containers.length - 1 ? "none" : "";
        }
    }

    function jumpToSlot(timeslot) {
        var firstItemInSlot = gallery.querySelector("div.container[data-timeslot='" + timeslot + "']");
        scrollToActiveItem(firstItemInSlot,ANIMATION_SMOOTH);
    }

    function getMostVisibleItem()
    {
        var scrollX = window.scrollX;
        var currentImageX = scrollX % activeItem.offsetWidth;
        var targetIndex = null;
        if( currentImageX / activeItem.offsetWidth > 0.5 )
        {
            targetIndex = (window.scrollX + activeItem.offsetWidth - currentImageX) / activeItem.offsetWidth;
        }
        else
        {
            targetIndex = (window.scrollX - currentImageX) / activeItem.offsetWidth;
        }

        return containers[targetIndex];
    }

    var tabticker = null;
    var tracker_current_offset = 0;
    var tracker_last_offset = 0;
    var tracker_velocity = 0;
    var tracker_timestamp = null;

    function tapstart(e)
    {
        if( e.target.classList.contains("button") ) return;

        //console.log("tabstart");
        tabStartPageX = e.detail.clientX;
        tabStartScrollX = window.scrollX;
        isTabMoving = false;
        isTabTouch = true;

        tracker_current_offset = e.detail.clientX;
        tracker_last_offset = e.detail.clientX;
        tracker_velocity = 0;
        tracker_timestamp = performance.now();
        tabticker = setInterval(tabtracker, 100);
    }

    function tabtracker()
    {
        var now = performance.now();

        var elapsed = now - tracker_timestamp;

        var delta = tracker_current_offset - tracker_last_offset;
        tracker_last_offset = tracker_current_offset;

        v = 1000 * delta / (1 + elapsed);
        tracker_velocity = 0.8 * v + 0.2 * tracker_velocity;

        tracker_timestamp = now;
    }

    function tapmove(e)
    {
        tracker_current_offset = e.detail.clientX;

        isTabMoving = true;
        //console.log("tapmove " + ( tabStartScrollX - diff ) );
        var diff = e.detail.clientX - tabStartPageX;
        window.scrollTo( tabStartScrollX - diff, 0 );
    }
    function tapend(e)
    {
        clearInterval(tabticker);

        if( isTabMoving )
        {
            isTabMoving = false;

            tabStartPageX = -1;

            if( tracker_velocity == 0 ) tabtracker();

            if (tracker_velocity > 500 )
            {
                var nextContainer = containers[parseInt(activeItem.dataset.index) - 1];
                if( typeof nextContainer != "undefined" )
                {
                    scrollToActiveItem(nextContainer,ANIMATION_CUSTOM);
                    return;
                }
            }
            else if( tracker_velocity < -500 )
            {
                var nextContainer = containers[parseInt(activeItem.dataset.index) + 1];
                if( typeof nextContainer != "undefined" )
                {
                    scrollToActiveItem(nextContainer,ANIMATION_CUSTOM);
                    return;
                }
            }

            scrollToActiveItem(getMostVisibleItem(),ANIMATION_SMOOTH);
        }

        window.setTimeout(function()
        {
            //console.log("touchend");
            isTabTouch = false;
        }, 10);
    }

    function scrollHandler(e){
        if( requestedScrollPosition == null || !checkRequestedPosition() )
        {
            return;
        }

        if( debug ) console.log("requestedScrollPosition reset");
        requestedScrollPosition = null;
        lastScrollPosition = null;
    }

    function checkRequestedPosition()
    {
        if( lastScrollPosition == null ) lastScrollPosition = requestedScrollPosition["source"];

        var currentScrollPosition = isFullscreen ? window.scrollX : window.scrollY;

        if( currentScrollPosition != lastScrollPosition )
        {
            //console.log(isForwardRequested + " " + isForwardActive + " " + currentScrollPosition + " " + lastScrollPosition);

            var isForwardRequested = requestedScrollPosition["target"] - requestedScrollPosition["source"] > 0;
            var isForwardActive = currentScrollPosition - lastScrollPosition > 0;
            lastScrollPosition = currentScrollPosition;

            if( isForwardRequested )
            {
                if( !isForwardActive )
                {
                    //console.log("forward");
                    return true;
                }
            }
            else
            {
                if( isForwardActive )
                {
                    //console.log("backward");
                    return true;
                }
            }
        }

        // offset of 1 is needed for chrome browser
        if( Math.abs( requestedScrollPosition["target"] - Math.round( isFullscreen ? window.scrollX : window.scrollY ) ) <= 1 )
        {
            return true;
        }

        return false;
    }

    function playIteration()
    {
        if( isPlaying == false ) return;
                
        var nextContainer = containers[parseInt(activeItem.dataset.index) - 1];
        if( typeof nextContainer == "undefined" )
        {
            stopPlay();
            return;
        }
        scrollToActiveItem(nextContainer,ANIMATION_INSTANT);
        
        nextContainer = containers[parseInt(activeItem.dataset.index) - 1];
        if( typeof nextContainer == "undefined" )
        {
            stopPlay();
            return;
        }
        var img = nextContainer.querySelector("img");
        if( img == null || img.naturalWidth  == 0 )
        { 
            //console.log("not loaded");
            var startTime = new Date().getTime();
            cancelLoading(nextContainer);
            loadImage(nextContainer,function(success)
            {
                var endTime = new Date().getTime();
                var diff = endTime - startTime;
                if( diff > 500 ) playIteration();
                else playTimer = window.setTimeout(playIteration,500-diff);
            });
        }
        else
        {
            playTimer = window.setTimeout(playIteration,500);
        }
    }
    function stopPlay(e)
    {
        if( e && e.target.classList.contains("button") && e.type == 'tapstart' ) return;

        isPlaying = false;

        if( playTimer != null )
        {
            window.clearTimeout(playTimer);
            playTimer = null;
        }
        
        galleryStartPlayButton.style.display = activeItem.dataset.index == 0 ? "none" : "";
        galleryStopPlayButton.style.display = "";
        
        document.removeEventListener("tapstart",stopPlay);
    }
    function startPlay(e)
    {
        isPlaying = true;

        galleryStartPlayButton.style.display = "none";
        galleryStopPlayButton.style.display = "inline";
        
        document.addEventListener("tapstart",stopPlay);
        
        playIteration();
    }
    function openDetails(index)
    { 
        if( isFullscreen ) return;
        isFullscreen = true;
        
        var layer = gallery.querySelector("div.layer");
        
        var item = containers[index];
        var img = item.querySelector("img");
        
        var scrollbarSize = window.innerWidth - document.documentElement.clientWidth;
        
        var sourceImgRect = img.getBoundingClientRect();
        var galleryRect = gallery.getBoundingClientRect();
        var galleryTop = galleryRect.top + window.scrollY;
        
        var targetLayerRect = {top: galleryTop, left: 0, width: window.innerWidth, height: window.innerHeight - galleryTop - scrollbarSize };
        var targetImgRect = {top: 0, left: 0, width: 0, height: 0 };
        var imgRatio = sourceImgRect.height / sourceImgRect.width;
        
        var ratio = targetLayerRect.width / sourceImgRect.width;
        if( sourceImgRect.height * ratio > targetLayerRect.height ) ratio = targetLayerRect.height / sourceImgRect.height;
        targetImgRect.height = sourceImgRect.height * ratio;
        targetImgRect.width = sourceImgRect.width * ratio;
        //if( targetImgRect.height > imageHeight ) targetImgRect.height = imageHeight;
        //if( targetImgRect.width > imageWidth ) targetImgRect.width = imageWidth;
        targetImgRect.top = targetLayerRect.top + ( targetLayerRect.height - targetImgRect.height ) / 2 - 1;
        targetImgRect.left = targetLayerRect.left + ( targetLayerRect.width - targetImgRect.width ) / 2 - 1;

        var t5 = performance.now()

        layer.style.cssText = "display: block; top: " + targetLayerRect.top + "px; left: " + targetLayerRect.left + "px; width: " + targetLayerRect.width + "px; height: " + targetLayerRect.height + "px";
        
        img.style.cssText = "position: fixed; z-index: 50; top: " + sourceImgRect.top + "px; left: " + sourceImgRect.left + "px; width: " + sourceImgRect.width + "px; height: " + sourceImgRect.height + "px;";
        
        // force refresh
        img.offsetHeight;
        
        window.setTimeout(function() { layer.style.opacity = "1.0"; }, 150);
        
        img.style.cssText = "position: fixed; z-index: 50; transition: all 0.3s; top: " + targetImgRect.top + "px; left: " + targetImgRect.left + "px; width: " + targetImgRect.width + "px; height: " + targetImgRect.height + "px;";

        window.setTimeout(function(){
            gallery.classList.add("fullscreen");
            
            gallery.addEventListener("tapstart",tapstart);
            gallery.addEventListener("tapmove",tapmove);
            gallery.addEventListener("tapend",tapend);

            layer.style.cssText = "";
            img.style.cssText = "";

            scrollToActiveItem(containers[index],ANIMATION_INSTANT);

            positionSlotTooltip();
        },300);
    }
    
    function closeDetails()
    {
        if( !isFullscreen ) return;
        isFullscreen = false;
        
        var layer = gallery.querySelector("div.layer");
        
        var img = activeItem.querySelector("img");

        var sourceImgRect = getOffset(img);
        sourceImgRect.left = img.offsetLeft;
        var sourceLayerRect = getOffset(activeItem);
        sourceLayerRect.left = 0;
        
        gallery.classList.remove("fullscreen");
        gallery.removeEventListener("tapstart",tapstart);
        gallery.removeEventListener("tapmove",tapmove);
        gallery.removeEventListener("tapend",tapend);
        
        scrollToActiveItem(activeItem,ANIMATION_INSTANT);

        var targetImgRect = getOffset(img);
        
        layer.style.cssText = "display: block; top: " + sourceLayerRect.top + "px; left: " + sourceLayerRect.left + "px; width: " + sourceLayerRect.width + "px; height: " + sourceLayerRect.height + "px; opacity: 1.0";

        img.style.cssText = "position: fixed; z-index: 50; top: " + sourceImgRect.top + "px; left: " + sourceImgRect.left + "px; width: " + sourceImgRect.width + "px; height: " + sourceImgRect.height + "px;";
        
        // force refresh
        img.offsetHeight;

        layer.style.opacity = "";
        
        img.style.cssText = "position: fixed; z-index: 50; transition: all 0.3s; top: " + targetImgRect.top + "px; left: " + targetImgRect.left + "px; width: " + targetImgRect.width + "px; height: " + targetImgRect.height + "px;";

        window.setTimeout(function(){
            layer.style.display = "";
            
            img.style.cssText = "";
            
            positionSlotTooltip();
        },300);
    }
  
    function jumpToPreviousImage()
    {
        scrollToActiveItem(containers[parseInt(activeItem.dataset.index) - 1],ANIMATION_SMOOTH);
    }
    
    function jumpToNextImage()
    {
        scrollToActiveItem(containers[parseInt(activeItem.dataset.index) + 1],ANIMATION_SMOOTH);
    }

    function updateList()
    {
        var url = mx.Host.getBase() + 'index_update.php';
        
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url );
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                var content = document.createElement("div");
                content.innerHTML = this.response;
                
                if( content.querySelector("#gallery") )
                {
                    var containerMap = {};
                    containers.forEach(function(container,index){
                        containerMap[container.dataset.src] = container;
                    });

                    var _containers = content.querySelector("#gallery").childNodes;
                    var _nextContainer = containers[0];
                    Object.values(_containers).forEach(function(container,index){
                        if( typeof containerMap[container.dataset.src] == "undefined" )
                        {
                            if( _nextContainer )
                            {
                                gallery.insertBefore(container,_nextContainer);
                            }
                            else
                            {
                                gallery.appendChild(container);
                            }
                            containerObserver.observe(container);
                        }
                        else
                        {
                            _nextContainer = containerMap[container.dataset.src].nextSibling;
                            containerMap[container.dataset.src].dataset.index = container.dataset.index;
                            delete containerMap[container.dataset.src];
                        }
                    });

                    var _activeItem = activeItem;
                    Object.values(containerMap).forEach(function(container,index){
                        container.parentNode.removeChild(container);
                        //console.log("remove image");
                        if( container.dataset.src == activeItem.dataset.src )
                        {
                            _activeItem = null;
                        }
                    });

                    if( _activeItem == null ) _activeItem = containers[0]

                    // refresh containers
                    containers = gallery.querySelectorAll(".container");

                    slotOverview.innerHTML = content.querySelector("#slots").innerHTML;
                    
                    // reset active states
                    activeItem = null;
                    activeSlot = null;
                    slotTooltipElement = null;
                    
                    if( ( isFullscreen ? window.scrollX : window.scrollY ) == 0 )
                    {
                        setActiveItem(containers[0]);
                    }
                    else
                    {
                        scrollToActiveItem(_activeItem,ANIMATION_INSTANT);
                    }
                }
        
                updateTimer = window.setTimeout(updateList,30000);
            }
            else 
            {
                updateTimer = mx.Page.handleRequestError(this.status,url,updateList,60000);
            }
        };
        
        var data = {};
        data['count'] = containers.length;
        data['sub'] = folder;
        
        xhr.send(JSON.stringify(data));
    }

    function delayedSlotPosition()
    {
        if( isFullscreen ) return;

        if( requestedScrollPosition != null )
        {
            if( debug ) console.log("delayedPositon: skipped");
            return;
        }

        var firstElement = visibleContainer[0];
        var minIndex = visibleContainer[0].dataset.index;
        visibleContainer.forEach(function(element,index){
            if( minIndex > element.dataset.index )
            {
                _firstElement = element;
                minIndex = element.dataset.index
            }
        });

        setActiveItem(firstElement);
    }

    var initObserverTimer;
    function initObserver()
    {
        if( window.innerWidth == 0 )
        {
            initObserverTimer = window.setTimeout(initObserver, 1);
            return;
        }

        if( containerObserver ) containerObserver.disconnect();

        // rootMargin does not work propperly on android devices in iframes
        var observerOptions = { rootMargin: ( ( galleryRect.top+window.scrollY ) * -1 ) + "px " + window.innerWidth + "px " + ( window.innerHeight / 2 ) + "px 0px" };

        containerObserver = new IntersectionObserver((entries, imgObserver) => {
            var activeItemUpdateNeeded = activeItem == null;

            entries.forEach((entry) => {
                if( entry.isIntersecting )
                {
                    activeItemUpdateNeeded = true;

                    if( !entry.target.dataset.loaded )
                    {
                        var id = window.setTimeout(function(){
                            entry.target.removeAttribute("data-timer");
                            loadImage(entry.target);
                        },100);
                        entry.target.dataset.timer = id;
                    }
                    visibleContainer.push(entry.target);
                }
                else
                {
                    if( activeItem == entry.target ) activeItemUpdateNeeded = true;

                    if( entry.target.dataset.timer )
                    {
                        window.clearTimeout(entry.target.dataset.timer);
                        entry.target.removeAttribute("data-timer");
                    }
                    var index = visibleContainer.indexOf(entry.target)
                    if( index != -1 ) visibleContainer.splice(index, 1);
                }
            });

            if( activeItemUpdateNeeded ) delayedSlotPosition();
        },observerOptions);

        containers.forEach( function(container,index){
            containerObserver.observe(container);
        });
    }

    ret.jumpToSlot = jumpToSlot;
    ret.jumpToPreviousImage = jumpToPreviousImage;
    ret.jumpToNextImage = jumpToNextImage;
    ret.openDetails = openDetails;
    ret.closeDetails = closeDetails;
    ret.startPlay = startPlay;
    ret.stopPlay = stopPlay;

    ret.init = function(_imageHeight,_imageWidth,_folder)
    {
        imageHeight = _imageHeight;
        imageWidth = _imageWidth;
        folder = _folder;
        
        slotOverview = document.querySelector(".slots");

        gallery = document.querySelector("#gallery");
        galleryPreviousButton = gallery.querySelector(".button.previous");
        galleryNextButton = gallery.querySelector(".button.next");
        galleryStartPlayButton = gallery.querySelector(".button.start");
        galleryStopPlayButton = gallery.querySelector(".button.stop");

        var style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = 'div.dummy { margin-top: ' + (imageHeight*100/imageWidth) + '%; }';
        document.getElementsByTagName('head')[0].appendChild(style);
        
        galleryRect = gallery.getBoundingClientRect();
        containers = gallery.querySelectorAll(".container");
        
        initObserver();

        document.addEventListener('scroll', scrollHandler);
        
        window.addEventListener('resize', function(e) {
            if( activeItem )
            {
                scrollToActiveItem(activeItem,ANIMATION_INSTANT);
                positionSlotTooltip();
            }
        });
        
        document.addEventListener('mouseup', function(e) {
            if( isFullscreen )
            {
                if( e.clientY > document.documentElement.clientHeight )
                {
                    scrollToActiveItem(activeItem,ANIMATION_SMOOTH);
                }
            }
        });
        
        document.addEventListener('mousemove', function(e) {
            var reference = e.target;
            if( !reference.classList ) return;
            
            if( reference.classList.contains("bar") )
            {
                reference = reference.parentNode;
            }
            if( !reference.classList.contains("slot") )
            {
                if( activeSlot ) setSlotTooltip(activeSlot);
                return;
            }
            
            setSlotTooltip(reference);
        });
        
        mx.Swipe.init();
    
        updateTimer = window.setTimeout(updateList,30000);
    }
    
    return ret;
})( mx.Gallery || {} );
