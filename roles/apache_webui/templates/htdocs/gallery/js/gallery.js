mx.Gallery = (function( ret ) {
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

    var visibleContainer = [];
    
    var containerObserver = null;
    
    var tabStartPageX = -1;
    var tabStartScrollX = -1;
    var isTabMoving = false;
    var momentumScrollTimer = null;

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
    function delayedLoading(element)
    {
        if( !element.dataset.loaded )
        {
            var id = window.setTimeout(function(){ loadImage(element); },100);
            element.dataset.timer = id;
        }
    }
    
    function cancelLoading(element)
    {
        if( element.dataset.timer ) 
        {
            window.clearTimeout(element.dataset.timer);
            element.removeAttribute("data-timer");
        }
    }

    function scrollToActiveItem(item,animated)
    {
        if( isFullscreen )
        {
            if( Math.round(window.scrollX) != item.offsetLeft )
            {
                if( debug ) console.log("scrollToActiveItem: " + item.dataset.formattedtime);
    
                requestedScrollPosition = { source: window.scrollX, target: item.offsetLeft };
                window.scrollTo({
                  left: requestedScrollPosition["target"],
                  behavior: animated ? 'smooth' : 'auto'
                });
            }
        }
        else
        {
            var targetPosition = item.offsetTop - gallery.offsetTop;
            if( Math.round(window.scrollY) != targetPosition )
            {
                if( debug ) console.log("scrollToActiveItem: " + item.dataset.formattedtime);

                requestedScrollPosition = { source: window.scrollY, target: targetPosition };
                window.scrollTo({
                  top: requestedScrollPosition["target"],
                  behavior: animated ? 'smooth' : 'auto'
                });
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
            galleryPreviousButton.style.display = activeItem.dataset.index == 0 ? "none" : "";
            galleryNextButton.style.display = activeItem.dataset.index == containers.length - 1 ? "none" : "";
        }
    }

    function jumpToSlot(timeslot) {
        var firstItemInSlot = gallery.querySelector("div.container[data-timeslot='" + timeslot + "']");
        scrollToActiveItem(firstItemInSlot,true);
    }

    function processMomentingScroll()
    {
        if( momentumScrollTimer ) window.clearTimeout(momentumScrollTimer);
        
        momentumScrollTimer = window.setTimeout(function()
        {
            momentumScrollTimer = null;
            scrollToActiveItem(getMostVisibleItem(),true);
        },200);
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
    function tapstart(e)
    {
        if( e.target.classList.contains("button") )
        {
            return;
        }
        
        //console.log("tabstart");
        tabStartPageX = e.detail.clientX;
        tabStartScrollX = window.scrollX;
        isTabMoving = false;
    }
    function tapmove(e)
    {
        isTabMoving = true;
        //console.log("tapmove " + ( tabStartScrollX - diff ) );
        var diff = e.detail.clientX - tabStartPageX;
        window.scrollTo( tabStartScrollX - diff, 0 );
    }
    function tapend(e)
    {
        if( !isTabMoving ) return;
        isTabMoving = false;
        
        //console.log("tapend");
        tabStartPageX = -1;
        
        if( mx.Core.isTouchDevice() )
        {
            processMomentingScroll();
        }
        else
        {
            scrollToActiveItem(getMostVisibleItem(),true);
        }
    }

    function playIteration()
    {
        if( isPlaying == false ) return;
                
        //console.log("play");
        var nextContainer = containers[parseInt(activeItem.dataset.index) + 1];
        scrollToActiveItem(nextContainer,false);
        
        nextContainer = containers[parseInt(activeItem.dataset.index) + 1];
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
    function stopPlay()
    {
        isPlaying = false;

        if( playTimer != null )
        {
            window.clearTimeout(playTimer);
            playTimer = null;
        }
        
        galleryStartPlayButton.style.display = "";
        galleryStopPlayButton.style.display = "";
        
        document.removeEventListener("tapstart",stopPlay);
    }
    function startPlay()
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
        if( targetImgRect.height > imageHeight ) targetImgRect.height = imageHeight;
        if( targetImgRect.width > imageWidth ) targetImgRect.width = imageWidth;
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

            scrollToActiveItem(containers[index],false);

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
        
        scrollToActiveItem(activeItem,false);

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
        scrollToActiveItem(containers[parseInt(activeItem.dataset.index) - 1],true);
    }
    
    function jumpToNextImage()
    {
        scrollToActiveItem(containers[parseInt(activeItem.dataset.index) + 1],true);
    }
    
    function delayedPosition()
    {
        if( requestedScrollPosition != null )
        {
            if( debug ) console.log("delayedPositon: skipped");
            return;
        }
        
        var offsetReference = Math.round( isFullscreen ? window.scrollX : window.scrollY);
        
        var galleryRect = gallery.getBoundingClientRect();
        var galleryTop = galleryRect.top + window.scrollY;
        
        var firstElement = null;
        var firstElementRect = null;
        
        visibleContainer.forEach(function(element,index){
            var elementRect = element.getBoundingClientRect();
        
            if( isFullscreen )
            {
                if( elementRect.left < -2 )
                {
                    return;
                }
            
                if( firstElement == null 
                    || firstElementRect.left > elementRect.left
                    || firstElementRect.left == elementRect.left
                ){
                    firstElement = element;
                    firstElementRect = elementRect;
                }
            }
            else
            {
                //console.log(element.dataset.formattedtime);
                if( elementRect.top + elementRect.height < galleryTop - 2 )
                {
                    return;
                }
            
                if( firstElement == null 
                    || firstElementRect.top > elementRect.top
                    || ( firstElementRect.top == elementRect.top && firstElementRect.left > elementRect.left )
                ){
                    firstElement = element;
                    firstElementRect = elementRect;
                }
            }
        });
        
        if( firstElement != null )
        {
            //console.log(firstElement.dataset.formattedtime);
            if( debug ) console.log("delayedPositon: " + firstElement.dataset.formattedtime);
            setActiveItem(firstElement);
        }
        else
        {
            if( debug ) console.log("delayedPositon: notfound");
        }
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
    
    function scrollHandler(e){
        if( requestedScrollPosition != null )
        {
            if( checkRequestedPosition() )
            {
                if( debug ) console.log("requestedScrollPosition reset");
                requestedScrollPosition = null;
                lastScrollPosition = null;
            }
            return;
        }
        
        if( isFullscreen )
        {
            if( !isTabMoving ) processMomentingScroll();
        }
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
                    var _containers = content.querySelector("#gallery").childNodes;
                    
                    var containerMap = {};
                    containers.forEach(function(container,index){
                        containerMap[container.dataset.src] = index;
                    });
                    
                    var currentIndex = 0;//containers[0];
                    var _containerMap = {};
                    _containers.forEach(function(container,index){
                        _containerMap[container.dataset.src] = index;

                        if( typeof containerMap[container.dataset.src] == "undefined" )
                        {
                            gallery.insertBefore(container,containers[currentIndex]);
                            containerObserver.observe(container);
                            //console.log("add image");
                        }
                        else
                        {
                            currentIndex = containerMap[container.dataset.src] + 1;
                        }
                    });
                    
                    var _activeItem = activeItem;
                    containers.forEach(function(container,index){
                        if( typeof _containerMap[container.dataset.src] == "undefined" )
                        {
                            container.parentNode.removeChild(container);
                            //console.log("remove image");
                            if( container.dataset.src == activeItem.dataset.src )
                            {
                                _activeItem = null;
                            }
                        }
                        else if(_activeItem == null)
                        {
                            _activeItem = container;
                        }
                    });
                    
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
                        scrollToActiveItem(_activeItem,false);
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

    function initObserver()
    {
        var observerOptions = {
            rootMargin: ( ( galleryRect.top+window.scrollY ) * -1 ) + "px 0px 0px 0px"
        };
        containerObserver = new IntersectionObserver((entries, imgObserver) => {        
            var activeItemUpdateNeeded = activeItem == null;
            
            entries.forEach((entry) => {
                if(entry.isIntersecting) 
                {
                    activeItemUpdateNeeded = true;
                    
                    delayedLoading(entry.target);
                    visibleContainer.push(entry.target);
                }
                else
                {
                    if( activeItem == entry.target ) activeItemUpdateNeeded = true;

                    cancelLoading(entry.target);
                    var index = visibleContainer.indexOf(entry.target)
                    if( index != -1 )
                    {
                        visibleContainer.splice(index, 1);
                    }
                }
            });
            
            if( activeItemUpdateNeeded ) delayedPosition();
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
                scrollToActiveItem(activeItem,false);
                positionSlotTooltip();
            }
        });
        
        document.addEventListener('mouseup', function(e) {
            if( isFullscreen )
            {
                if( e.clientY > document.documentElement.clientHeight )
                {
                    scrollToActiveItem(activeItem,true);
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
