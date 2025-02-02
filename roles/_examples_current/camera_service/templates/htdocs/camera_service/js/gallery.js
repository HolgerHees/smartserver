mx.GalleryAnimation = (function( ret ) {
    ret.TYPE_INSTANT = "instant";
    ret.TYPE_SMOOTH = "smooth";

    var requestId = null;
    var startPos = null;
    var diff = null;
    var duration = null;
    var startTime = null;
    var currentPos = null;

    var isHorizontal = null;

    ret.scrollTo = function(options)
    {
        if( options["behavior"] == mx.GalleryAnimation.TYPE_INSTANT )
        {
            mx.GalleryAnimation.stop();
            window.scrollTo(options);
        }
        else
        {
            isHorizontal = "left" in options;
            if( isHorizontal )
            {
                // scrollX is not 100% reliable during animations on mobile devices.
                startPos = currentPos == null ? window.scrollX : currentPos;
                diff = options["left"] - startPos;
                duration = Math.abs(diff) * 800 / window.innerWidth;
            }
            else
            {
                // scrollY is not 100% reliable during animations on mobile devices.
                startPos = currentPos == null ? window.scrollY : currentPos;
                diff = options["top"] - startPos;
                duration = Math.abs(diff) * 800 / window.innerHeight;
            }

            if( duration > 2000 ) duration = 2000;
            startTime = null;

            if( requestId != null ) return;

            const loop = function (currentTime) {
                if( requestId == null ) return;

                if (!startTime) startTime = currentTime;

                const time = currentTime - startTime;
                const percent = Math.min(time / duration, 1);
                // https://easings.net/de => easeOutCubic
                const animation = function (x) { return 1 - Math.pow(1 - x, 3); };

                currentPos = startPos + diff * animation(percent);
                if( isHorizontal ) window.scrollTo(currentPos, 0);
                else window.scrollTo(0, currentPos);

                // Continue moving
                if (time < duration) requestId = window.requestAnimationFrame(loop);
                else requestId = currentPos = null;
            };
            requestId = window.requestAnimationFrame(loop);
        }
    }

    ret.isScrolling = function()
    {
        return requestId != null;
    }

    ret.stop = function()
    {
        if( requestId == null ) return;

        window.cancelAnimationFrame(requestId);
        requestId = currentPos = null;
    }

    return ret;
})( mx.GalleryAnimation || {} );

mx.GallerySwipeHandler = (function( ret ) {
    var isMoving = false;
    var startScrollX = 0;
    var startClientX = 0;
    var currentClientX = 0;
    var currentClientY = 0;

    var tabticker = null;
    var trackerLastClientX = 0;
    var trackerVelocity = 0;
    var trackerTimestamp = null;

    var swipeCallback = null;
    var swipeElement = null;

    function tabtracker()
    {
        var now = performance.now();
        var elapsed = now - trackerTimestamp;
        var delta = currentClientX - trackerLastClientX;

        trackerLastClientX = currentClientX;

        v = 1000 * delta / (1 + elapsed);
        trackerVelocity = 0.8 * v + 0.2 * trackerVelocity;

        trackerTimestamp = now;
    }

    function tapstart(e)
    {
        if( e.target.classList.contains("button") && !e.target.classList.contains("next") && !e.target.classList.contains("previous") ) return;

        isMoving = false;
        startScrollX = window.scrollX;
        startClientX = e.detail.clientX;
        currentClientX = startClientX;

        trackerLastClientX = startClientX;
        trackerVelocity = 0;
        trackerTimestamp = performance.now();
        tabticker = setInterval(tabtracker, 100);

        swipeElement.addEventListener("tapmove",tapmove);
        swipeElement.addEventListener("tapend",tapend);
    }

    function tapmove(e)
    {
        if( !isMoving ) mx.GalleryAnimation.stop();

        isMoving = true;
        currentClientX = e.detail.clientX;
        currentClientY = e.detail.clientY;

        var diff = currentClientX - startClientX;
        mx.GalleryAnimation.scrollTo({"left": startScrollX - diff, "behavior": mx.GalleryAnimation.TYPE_INSTANT});
    }

    function tapend(e)
    {
        clearInterval(tabticker);

        swipeElement.removeEventListener("tapmove",tapmove);
        swipeElement.removeEventListener("tapend",tapend);

        if( !isMoving ) return;

        if( e.target.classList.contains("button") )
        {
            let elements = document.elementsFromPoint(currentClientX, currentClientY);
            if( elements[0].classList.contains("button") )
            {
                mx.GalleryAnimation.scrollTo({"left": startScrollX, "behavior": mx.GalleryAnimation.TYPE_INSTANT});
                return;
            }
        }

        if( trackerVelocity == 0 ) tabtracker();

        swipeCallback(trackerVelocity);
    }

    ret.enable = function(element, callback)
    {
        swipeCallback = callback;
        swipeElement = element;

        element.addEventListener("tapstart",tapstart);
    }

    ret.disable = function()
    {
        swipeElement.removeEventListener("tapstart",tapstart);
    }

    return ret;
})( mx.GallerySwipeHandler || {} );

mx.Gallery = (function( ret ) {
    var isFullscreen = false;
    
    var listData = null;

    var activeItem = null;
    var activeSlot = null;
    var slotTooltipElement = null;

    var dynamicStyle = null;
    var slotOverview = null;

    var gallery = null;
    var galleryPreviousButton = null;
    var galleryNextButton = null;
    var galleryPlayButton = null;
    var galleryCloseButton = null;
  
    var containerObserver = null;
    var visibleContainer = [];

    var playTimer = null;
    var isPlaying = false;

    var updateStateFlag = null;
    var updateStateTimer = null;

    function getItemIndex(item)
    {
        return listData["images"].findIndex(function(data){ return data["item"] == item; });
    }

    function getItemByIndex(index)
    {
        if( index < 0 || index >= listData["images"].length ) return null;
        return listData["images"][index]["item"];
    }

    function buildAspectRationStyle()
    {
        if( !dynamicStyle )
        {
            dynamicStyle = document.createElement('style');
            dynamicStyle.type = 'text/css';
            document.getElementsByTagName('head')[0].appendChild(dynamicStyle);
        }
        dynamicStyle.innerHTML = '#gallery:not(.fullscreen) > div.container { aspect-ratio: ' + (listData["width"] / listData["height"]) + '; }';
    }

    function buildSlot(datetime)
    {
        datetime.setMinutes(0);
        datetime.setSeconds(0);
        datetime.setMilliseconds(0);

        return datetime;
    }

    function buildSlots(){
        slotOverview.innerHTML = "";

        var images = listData["images"];

        if( images.length == 0 )
        {
            let div = document.createElement("div");
            div.style.margin = "auto";
            div.innerText = mx.I18N.get( "No images available" );
            slotOverview.appendChild(div);
            return;
        }

        var starttime = buildSlot(new Date(images[0]["timestamp"] * 1000));

        var endtime = buildSlot(new Date(images[images.length-1]["timestamp"] * 1000));

        var hours = Math.floor( ( starttime.getTime() - endtime.getTime() ) / ( 60 * 60 * 1000 ) );

        //var max_steps = 100;
        var stepDurationInHours = 1;//Math.ceil(hours / max_steps);

        var grouped_images = [];
        var currenttimestamp = starttime.getTime();

        while( currenttimestamp >= endtime.getTime() )
        {
            grouped_images[currenttimestamp] = [];
            currenttimestamp -= ( stepDurationInHours * 60 * 60 * 1000);
        }

        images.forEach(function(entry)
        {
            var slottime = buildSlot(new Date(entry["timestamp"] * 1000));
            grouped_images[slottime.getTime()].push(entry);
        });

        var max_count = 0;
        Object.entries(grouped_images).forEach(function([key, values])
        {
            if( max_count < values.length ) max_count = values.length;
        });

        function addLeadingZero(num)
        {

            var s = "0" + num;
            return s.substr(s.length-size);
        }

        var html = "";
        var lastLabledDate = null;
        var lastLabledTime = null;
        Object.entries(grouped_images).forEach(function([key, values])
        {
            var currenttime = new Date(parseInt(key));

            let slotDIV = document.createElement("div");
            slotDIV.classList.add("slot");

            if( values.length > 0 )
            {
                slotDIV.classList.add("filled");
                slotDIV.setAttribute("onclick", "mx.Gallery.jumpToSlot(" + key + ")");
            }

            if( values.length > 0 )
            {
                slotDIV.dataset.formattedtime = String(currenttime.getDate()).padStart(2, '0') + "." + String(currenttime.getMonth() + 1).padStart(2, '0') + ". " + String(currenttime.getHours() + 1).padStart(2, '0') + ":00";
                slotDIV.dataset.count = values.length;
            }

            slotDIV.dataset.timeslot = currenttime.getTime();

            if( lastLabledDate == null || lastLabledDate.getDay() != currenttime.getDay() )
            {
                let div = document.createElement("div");
                div.classList.add("date");
                div.innerText = String(currenttime.getDate()).padStart(2, '0') + "." + String(currenttime.getMonth() + 1).padStart(2, '0');
                slotDIV.appendChild(div);
                lastLabledDate = currenttime;
            }

            if( lastLabledTime == null || lastLabledTime.getTime() - currenttime.getTime() > (60*60*12*1000) )
            {
                let div = document.createElement("div");
                div.classList.add("time");
                div.innerText = String(currenttime.getHours() + 1).padStart(2, '0') + ":" + String(currenttime.getMinutes()).padStart(2, '0');
                slotDIV.appendChild(div);
                lastLabledTime = currenttime;
            }

            let div = document.createElement("div");
            div.classList.add("bar");
            if( values.length > 0 )
            {
                div.style.height = Math.ceil( values.length * 100 / max_count ) + "%";
            }
            else
            {
                div.style.height = 0;
            }
            slotDIV.appendChild(div);

            slotOverview.appendChild(slotDIV);
        });
    }

    function buildContainer(element_data){
        var container = document.createElement("div");
        container.classList.add("container");
        container.setAttribute("onclick", "mx.Gallery.openDetails(this)" );
        container.dataset.name = element_data["name"];
        var datetime = new Date(element_data["timestamp"] * 1000);
        container.dataset.formatted = String(datetime.getDate()).padStart(2, '0') + "." + String(datetime.getMonth() + 1).padStart(2, '0') + ". " + String(datetime.getHours()).padStart(2, '0') + ":" + String(datetime.getMinutes()).padStart(2, '0') + ":" + String(datetime.getSeconds()).padStart(2, '0');
        container.dataset.src = element_data["name"] + ".jpg";
        container.dataset.small_src = element_data["name"] + "_small.jpg";
        container.dataset.medium_src = element_data["name"] + "_medium.jpg";
        container.dataset.timeslot = buildSlot(datetime).getTime();
        return container;
    }

    function buildContainers()
    {
        gallery.querySelectorAll(".container").forEach(e => e.parentNode.removeChild(e));
        listData["images"].forEach(function(element_data){ element_data["item"] = buildContainer(element_data); gallery.appendChild(element_data["item"]); });
    }

    function updateContainers(data)
    {
        if( !listData ) return;

        if( updateStateTimer ) window.clearTimeout(updateStateTimer);
        updateStateFlag = true;

        var startScroll = isFullscreen ? window.scrollX : window.scrollY;
        var startOffset = isFullscreen ? gallery.offsetWidth : gallery.offsetHeight;

        var _activeItem = activeItem;

        data["removed"].forEach(function(name)
        {
            var index = listData["images"].findIndex(function(_data){
                return _data["name"] == name;
            });
            if( index != -1 )
            {
                var item = getItemByIndex(index);
                item.parentNode.removeChild(item);
                listData["images"].splice(index, 1);
                if( _activeItem == item ) _activeItem = null;
            }
        });
        data["added"].forEach(function(_data)
        {
            var index = listData["images"].findIndex(function(__data){
                if( __data["timestamp"] > _data["timestamp"] ) return false;
                if( __data["name"] > _data["name"] ) return false;
                return true;
            });

            if( index != -1 )
            {
                var refNode = getItemByIndex(index);
                var container = buildContainer(_data);
                _data["item"] = container;
                refNode.parentNode.insertBefore(container,refNode);
                listData["images"].splice(index,0,_data);

                containerObserver.observe(container);
            }
        });
        var endOffset = isFullscreen ? gallery.offsetWidth : gallery.offsetHeight;

        buildSlots();

        // reset active states
        activeItem = null;
        activeSlot = null;
        slotTooltipElement = null;

        if( startScroll == 0 )
        {
            setActiveItem(getItemByIndex(0));
        }
        else
        {
            if( _activeItem == null ) _activeItem = getItemByIndex(0);

            setActiveItem(_activeItem);

            if( isFullscreen ) mx.GalleryAnimation.scrollTo({ left: startScroll + (endOffset - startOffset), behavior: mx.GalleryAnimation.TYPE_INSTANT });
            else mx.GalleryAnimation.scrollTo({ top: startScroll + (endOffset - startOffset), behavior: mx.GalleryAnimation.TYPE_INSTANT });
        }

        updateStateFlag = false
        updateStateTimer = window.setTimeout(function(){ updateStateTimer = updateStateFlag = null; },250);
    }

    function resetUpdateStateFlag()
    {
        if( updateStateTimer ) window.clearTimeout(updateStateTimer);
        updateStateTimer = updateStateFlag = null;
    }

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

    function getNextItem(item)
    {
        var index = getItemIndex((item ? item : activeItem)) - 1;
        return getItemByIndex(index);
    }

    function getPreviousItem(item)
    {
        var index = getItemIndex((item ? item : activeItem)) + 1;
        return getItemByIndex(index);
    }

    function positionSlotTooltip()
    {
        if( !slotTooltipElement.dataset.count )
        {
            mx.Tooltip.hide();
            return;
        }

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
    
    function setSlotTooltip(element)
    {
        if( element == slotTooltipElement ) return;
        
        if( slotTooltipElement != null ) slotTooltipElement.classList.remove("active");
        
        slotTooltipElement = element;
        slotTooltipElement.classList.add("active");
        
        positionSlotTooltip();
    }

    function slotHoverHandler(e)
    {
        var reference = e.target;
        if( !reference.classList ) return;

        if( reference.classList.contains("bar") ) reference = reference.parentNode;

        if( !reference.classList.contains("slot") )
        {
            if( activeSlot ) setSlotTooltip(activeSlot);
            return;
        }

        setSlotTooltip(reference);
    }
    
    function missingImageSize(element)
    {
        var imageSize = isFullscreen ? 3: ( window.devicePixelRatio > 1 ? 2 : 1 );
        return element.dataset.loaded >= imageSize ? 0 : imageSize;
    }

    function loadImage(element,callback)
    {
        var imageSize = missingImageSize(element);
        if( !imageSize )
        {
            if( callback ) console.error("should never happen " + imageSize);
            return;
        }
        element.dataset.loaded = imageSize;

        var img = element.querySelector("img");
        if( !img ) img = document.createElement("img");

        if( callback )
        {
            img.onload = function() { callback(true); };
            img.onerror = function() { callback(false); };
        }

        if( imageSize == 3 ) img.src = "./cache/" + listData["camera_name"] + "/" + element.dataset.src;
        else if( imageSize == 2 ) img.src = "./cache/" + listData["camera_name"] + "/" + element.dataset.medium_src;
        else img.src = "./cache/" + listData["camera_name"] + "/" + element.dataset.small_src;

        if( !img.parentNode)
        {
            var timeLabel = document.createElement("span");
            timeLabel.innerHTML = element.dataset.formatted;
            element.appendChild(timeLabel);

            var srcLabel = document.createElement("span");
            srcLabel.innerHTML = element.dataset.name;
            element.insertBefore(srcLabel, element.firstChild);

            element.insertBefore(img, element.firstChild);
            element.addEventListener("dragstart",function(e){ e.preventDefault(); });
        }
    }

    function delayedLoading(element)
    {
        if( element.dataset.timer || !missingImageSize(element) ) return;

        var id = window.setTimeout(function(){ element.removeAttribute("data-timer"); loadImage(element); },100);
        element.dataset.timer = id;
    }

    function cancelLoading(element)
    {
        if( !element.dataset.timer ) return;

        window.clearTimeout(element.dataset.timer);
        element.removeAttribute("data-timer");
    }

    function scrollToActiveItem(item,behavior)
    {
        if( isFullscreen )
        {
            if( Math.round(window.scrollX) != item.offsetLeft ) mx.GalleryAnimation.scrollTo({ left: item.offsetLeft, behavior: behavior });
        }
        else
        {
            var targetPosition = item.offsetTop - gallery.offsetTop;
            if( Math.round(window.scrollY) != targetPosition ) mx.GalleryAnimation.scrollTo({ top: targetPosition, behavior: behavior });
        }
        
        setActiveItem(item);
    }
    
    function setActiveItem(item)
    {
        if( item != activeItem )
        {
            if( activeItem == null || activeItem.dataset.timeslot != item.dataset.timeslot )
            {
                if( activeItem != null ) activeSlot.classList.remove("active");
                activeSlot = slotOverview.querySelector(".slot[data-timeslot=\"" + item.dataset.timeslot + "\"]");
                activeSlot.classList.add("active");
                setSlotTooltip(activeSlot);
            }
            activeItem = item;

            if( isFullscreen )
            {
                var previousItem = getPreviousItem();
                if( previousItem != null ) delayedLoading(previousItem);

                var nextItem = getNextItem();
                if( nextItem != null ) delayedLoading(nextItem);
            }
        }

        if( isFullscreen ) alignGalleryButtons(activeItem);
    }

    function alignGalleryButtons(item)
    {
        galleryPlayButton.style.transform = item == getItemByIndex(0) ? "" : "translate(0)";
        galleryNextButton.style.transform = item == getItemByIndex(0) ? "" : "translate(0)";
        galleryPreviousButton.style.transform = item == getItemByIndex(listData["images"].length - 1) ? "" : "translate(0)";
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

        return getItemByIndex(targetIndex);
    }

    function delayedSlotPosition()
    {
        if( isFullscreen || visibleContainer.length == 0 ) return;

        if( mx.GalleryAnimation.isScrolling() ) return;

        if( updateStateFlag !== null ) return;

        var firstElement = visibleContainer[0];
        var minIndex = getItemIndex(visibleContainer[0]);
        visibleContainer.forEach(function(element,index){
            let _index = getItemIndex(element);
            if( minIndex > _index )
            {
                firstElement = element;
                minIndex = _index;
            }
        });

        setActiveItem(firstElement);
    }

    function initObserver()
    {
        var galleryRect = gallery.getBoundingClientRect();
        var observerOptions = { root: document, rootMargin: ( ( galleryRect.top + 1 ) * -1 ) + "px 0px 0px 0px" };

        var activeItemUpdateNeeded = true;
        containerObserver = new IntersectionObserver((entries, imgObserver) => {
            var isInitialLoading = activeItem == null;
            entries.forEach((entry) => {
                if( entry.isIntersecting )
                {
                    activeItemUpdateNeeded = true;
                    if( isInitialLoading || !mx.GalleryAnimation.isScrolling() ) loadImage(entry.target); // mx.GalleryAnimation.isScrolling() == false : if touch or mouse initiated scrolling
                    else delayedLoading(entry.target);
                    visibleContainer.push(entry.target);
                }
                else if( !isInitialLoading )
                {
                    if( activeItem == entry.target ) activeItemUpdateNeeded = true;
                    cancelLoading(entry.target);
                    var index = visibleContainer.indexOf(entry.target);
                    if( index != -1 ) visibleContainer.splice(index, 1);
                }
            });

            if( activeItemUpdateNeeded )
            {
                delayedSlotPosition();
                activeItemUpdateNeeded = false;
            }

            // avoid a delayedSlotPosition as a result of an update process
            if( updateStateFlag === false ) resetUpdateStateFlag();
        },observerOptions);

        listData["images"].forEach( function(data,index){ containerObserver.observe(data["item"]); });
    }

    function swipeHandler(velocity)
    {
        var item = null, direction = 0;

        if (velocity > 500 )
        {
            item = getNextItem();
            direction = -1;
        }
        else if( velocity < -500 )
        {
            item = getPreviousItem();
            direction = 1;
        }

        if( item != null )
        {
            scrollToActiveItem(item, mx.GalleryAnimation.TYPE_SMOOTH);
        }
        else
        {
            scrollToActiveItem(getMostVisibleItem(),mx.GalleryAnimation.TYPE_SMOOTH);
        }
    }

    function playIteration()
    {
        if( isPlaying == false ) return;

        var item = getNextItem();
        if( item == null )
        {
            mx.Gallery.stopPlay();
            return;
        }
        scrollToActiveItem(item,mx.GalleryAnimation.TYPE_INSTANT);

        item = getNextItem();
        if( item == null )
        {
            mx.Gallery.stopPlay();
            return;
        }
        if( missingImageSize(item) )
        {
            var startTime = new Date().getTime();
            cancelLoading(item);
            loadImage(item,function(success)
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

    function resizeHandler()
    {
        if( !activeItem ) return;

        scrollToActiveItem(activeItem,mx.GalleryAnimation.TYPE_INSTANT);
        positionSlotTooltip();
    }

    function keyHandler(e)
    {
        e.preventDefault();

        if( isPlaying ) mx.Gallery.stopPlay();

        if( e["key"] == "ArrowLeft" ) mx.Gallery.jumpToNextImage();
        else if( e["key"] == "ArrowRight" ) mx.Gallery.jumpToPreviousImage();
    }

    var openerDetails = null;
    ret.openDetails = function(item)
    {
        if( isFullscreen ) return;
        isFullscreen = true;

        openerDetails = { "visible_items": visibleContainer.map(function(visibleItem){ return visibleItem; }), "top": window.scrollY };

        loadImage(item);

        mx.GallerySwipeHandler.enable(gallery, swipeHandler);
        window.addEventListener("keydown",keyHandler);

        var layer = gallery.querySelector("div.layer");
        var img = item.querySelector("img");

        galleryCloseButton.style.transform = "translate(0)";
        alignGalleryButtons(item);

        var scrollbarSize = window.innerWidth - document.documentElement.clientWidth;

        var sourceImgRect = img.getBoundingClientRect();
        var galleryRect = gallery.getBoundingClientRect();
        var galleryTop = galleryRect.top + window.scrollY;

        var targetLayerRect = {top: galleryTop, left: 0, width: window.innerWidth, height: window.innerHeight - galleryTop - scrollbarSize };
        var targetImgRect = {top: 0, left: 0, width: 0, height: 0 };
        var imgRatio = sourceImgRect.height / sourceImgRect.width;

        targetImgRect.height = targetLayerRect.height;
        targetImgRect.width = targetLayerRect.width
        targetImgRect.top = targetLayerRect.top;
        targetImgRect.left = targetLayerRect.left;

        layer.style.cssText = "display: block; top: " + targetLayerRect.top + "px; left: " + targetLayerRect.left + "px; width: " + targetLayerRect.width + "px; height: " + targetLayerRect.height + "px";
        img.style.cssText = "position: fixed; z-index: 50; top: " + sourceImgRect.top + "px; left: " + sourceImgRect.left + "px; width: " + sourceImgRect.width + "px; height: " + sourceImgRect.height + "px;";

        // force refresh
        img.offsetHeight;

        layer.style.opacity = "1.0";
        img.style.cssText = "position: fixed; z-index: 50; transition: all 0.3s; top: " + targetImgRect.top + "px; left: " + targetImgRect.left + "px; width: " + targetImgRect.width + "px; height: " + targetImgRect.height + "px;";

        item.style.backgroundColor = "black";

        window.setTimeout(function(){
            gallery.classList.add("fullscreen");
            item.style.backgroundColor = "";

            layer.style.cssText = "";
            img.style.cssText = "";

            scrollToActiveItem(item,mx.GalleryAnimation.TYPE_INSTANT);
            positionSlotTooltip();
        },300);
    }

    ret.closeDetails = function()
    {
        if( !isFullscreen ) return;
        isFullscreen = false;

        mx.GalleryAnimation.stop();

        mx.GallerySwipeHandler.disable();
        window.removeEventListener("keydown",keyHandler);

        galleryNextButton.style.transform = "";
        galleryPreviousButton.style.transform = "";
        galleryPlayButton.style.transform = "";
        galleryCloseButton.style.transform = "";

        var layer = gallery.querySelector("div.layer");
        var img = activeItem.querySelector("img");
        if( img )
        {
            activeItem.style.backgroundColor = "black";

            var sourceImgRect = getOffset(img);
            sourceImgRect.left = img.offsetLeft;
            var sourceLayerRect = getOffset(activeItem);
            sourceLayerRect.left = 0;

            gallery.classList.remove("fullscreen");

            if( openerDetails["visible_items"].includes(activeItem) ) mx.GalleryAnimation.scrollTo({"top": openerDetails["top"], "behavior": mx.GalleryAnimation.TYPE_INSTANT});
            else scrollToActiveItem(activeItem,mx.GalleryAnimation.TYPE_INSTANT);
            openerDetails = null;

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
                activeItem.style.backgroundColor = "";

                positionSlotTooltip();
            },300);
        }
        else
        {
            gallery.classList.remove("fullscreen");

            if( openerDetails["visible_items"].includes(activeItem) ) mx.GalleryAnimation.scrollTo({"top": openerDetails["top"], "behavior": mx.GalleryAnimation.TYPE_INSTANT});
            else scrollToActiveItem(activeItem,mx.GalleryAnimation.TYPE_INSTANT);
            openerDetails = null;

            positionSlotTooltip();
        }
    }

    ret.tooglePlay = function(e )
    {
        if( !isPlaying ) mx.Gallery.startPlay();
        else mx.Gallery.stopPlay();
    }

    ret.startPlay = function()
    {
        isPlaying = true;

        galleryPlayButton.classList.remove("icon-play");
        galleryPlayButton.classList.add("icon-stop");

        document.addEventListener("tapstart",mx.Gallery.stopPlay);

        playIteration();
    }

    ret.stopPlay = function(e)
    {
        if( e && e.target.classList.contains("button") && e.target.classList.contains("play") && e.type == 'tapstart' ) return;

        isPlaying = false;

        galleryPlayButton.classList.add("icon-play");
        galleryPlayButton.classList.remove("icon-stop");

        if( playTimer != null )
        {
            window.clearTimeout(playTimer);
            playTimer = null;
        }

        galleryPlayButton.style.display = getItemIndex(activeItem) == 0 ? "" : "translate(0)";

        document.removeEventListener("tapstart",mx.Gallery.stopPlay);
    }

    ret.jumpToSlot = function(timeslot) {
        var firstItemInSlot = gallery.querySelector("div.container[data-timeslot='" + timeslot + "']");
        scrollToActiveItem(firstItemInSlot,mx.GalleryAnimation.TYPE_SMOOTH);
    }

    ret.jumpToPreviousImage = function()
    {
        var item = getPreviousItem();
        if( item == null ) return;
        scrollToActiveItem(item,mx.GalleryAnimation.TYPE_SMOOTH);
    }

    ret.jumpToNextImage = function()
    {
        var item = getNextItem();
        if( item == null ) return;
        scrollToActiveItem(item,mx.GalleryAnimation.TYPE_SMOOTH);
    }

    ret.update = function(data)
    {
        updateContainers(data);
    }

    ret.init = function(data)
    {
        mx.GalleryAnimation.scrollTo({"top": 0, "behavior": mx.GalleryAnimation.TYPE_INSTANT});

        listData = data;

        slotOverview = document.querySelector(".slots");
        buildSlots();

        gallery = document.querySelector("#gallery");
        galleryPreviousButton = gallery.querySelector(".button.previous");
        galleryNextButton = gallery.querySelector(".button.next");
        galleryPlayButton = gallery.querySelector(".button.play");
        galleryCloseButton = gallery.querySelector(".button.close");

        buildContainers();
        buildAspectRationStyle();
        
        if( document.readyState === 'complete' ) initObserver();
        else window.addEventListener('load', initObserver); // css must be applied to gallery

        window.addEventListener('resize', resizeHandler);
        document.addEventListener('mousemove', slotHoverHandler, {passive: true});
        
        mx.Swipe.init();
    }
    
    return ret;
})( mx.Gallery || {} );
