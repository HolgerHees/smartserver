<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta name="viewport" content="height=device-height, 
      width=device-width, initial-scale=1.0, 
      minimum-scale=1.0, maximum-scale=1.0, 
      user-scalable=no, target-densitydpi=device-dpi">
    <link href="https://fonts.googleapis.com/css?family=Open+Sans" rel="stylesheet"> 
    <link rel="stylesheet" href="/main/fonts/css/animation.css">
    <link rel="stylesheet" href="/main/fonts/css/fontello.css">
    <link href="css/main.css" rel="stylesheet"> 

    <script>var mx = { OnScriptReady: [], OnDocReady: [] };</script>
    
    <script src="/ressources?type=js"></script>
        
    <script>
        mx.OnScriptReady.push( function(){
            console.log("script ready");
        });

        mx.OnDocReady.push( function(){
            console.log("doc ready");
        });
	</script>
</head>
<body>
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
</script>
<?php
    include "inc/Image.php";
    include "inc/Folder.php";
    include "inc/Template.php";

    include "config.php";
    
    if( empty($_GET["sub"]) ) exit;
    $sub_folder = $_GET['sub'];
    
    $folder = new Folder($ftp_folder,$sub_folder);
    $images = $folder->getImages();
    
    list($width, $height, $type, $attr) = getimagesize($images[0]->getPath());
    
    $starttime = Template::getStarttime($images);
    $endtime = Template::getEndtime($images);
?>
<div class="tooltip"><span class="text"></span><span class="arrow"></span></div>
<div class="slots"><?php echo Template::getSlots($starttime,$endtime,$images); ?></div>
<div id="gallery">
  <div class="layer"></div>
  <span class="button previous icon-left" onclick="jumpToPreviousImage()"></span>
  <span class="button next icon-right" onclick="jumpToNextImage()"></span>
  <span class="button close icon-cancel" onclick="closeDetails()"></span>
<?php echo Template::getImages($images); ?>
</div>
<script> 
    var isFullscreen = false;
    
    var activeItem = null;
    var activeSlot = null;
    var slotTooltipElement = null;

    var imageHeight = <?php echo $height; ?>;
    var imageWidth = <?php echo $width; ?>;
    var folder = '<?php echo $sub_folder; ?>';
    var requestedScrollPosition = null;
    var debug = true;
    
    var slotOverview = document.querySelector(".slots");

    var tooltip = document.querySelector(".tooltip");
    var tooltipArrow = tooltip.querySelector(".arrow");
    
    var gallery = document.querySelector("#gallery");
    var galleryPreviousButton = gallery.querySelector(".button.previous");
    var galleryNextButton = gallery.querySelector(".button.next");
            
    var style = document.createElement('style');
    style.type = 'text/css';
    style.innerHTML = 'div.dummy { margin-top: ' + (imageHeight*100/imageWidth) + '%; }';
    document.getElementsByTagName('head')[0].appendChild(style);
    
    var galleryRect = gallery.getBoundingClientRect();
    
    var containers = gallery.querySelectorAll(".container");

    var visibleContainer = [];
    var observerOptions = {
        rootMargin: ( ( galleryRect.top+window.scrollY ) * -1 ) + "px 0px 0px 0px"
    };
    const containerObserver = new IntersectionObserver((entries, imgObserver) => {        
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
            tooltip.classList.remove("active");
        }
        else
        {
            tooltip.classList.add("active");
            tooltip.querySelector(".text").innerHTML = slotTooltipElement.dataset.formattedtime + "<br>" + slotTooltipElement.dataset.count + " Bilder";
            
            var slotOverviewRect = slotOverview.getBoundingClientRect();
            var slotRect = slotTooltipElement.getBoundingClientRect();
            var tooltipRect = tooltip.getBoundingClientRect();
            var tooltipArrowRect = tooltipArrow.getBoundingClientRect();
            
            var pos = ( slotRect.left + slotRect.width / 2 - tooltipRect.width / 2 )
            if( pos < 2 )
            {
                pos = 2;
                var center = slotRect.left + slotRect.width / 2;
                tooltipArrow.style.left = ( center - pos - tooltipArrowRect.width / 2 + 1) + "px";
            }
            else if( pos + tooltipRect.width > slotOverviewRect.width )
            {
                pos = slotOverviewRect.width - 2 - tooltipRect.width;
                var center = slotRect.left + slotRect.width / 2;
                tooltipArrow.style.left = ( center - pos - tooltipArrowRect.width / 2 + 1) + "px";
            }
            else
            {
                tooltipArrow.style.left = "calc(50% - " + (tooltipArrowRect.width / 2 - 1) + "px)";
            }
              
            tooltip.style.cssText = "left: " + pos + "px; top: 0px;";
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
    
    function delayedLoading(element)
    {
        var img = element.querySelector("img");
        if( !element.dataset.loaded )
        {
            var id = window.setTimeout(function(){ 
                element.addEventListener("dragstart",function(e){ e.preventDefault(); });
                var img = document.createElement("img");
                img.src = "image.php?sub=" + folder + "&image=" + element.dataset.src;
                element.appendChild(img);
                var label = document.createElement("span");
                label.innerHTML = element.dataset.formattedtime;
                element.appendChild(label);
                element.dataset.loaded = true;
            },100);
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

    var tabStartPageX = -1;
    var tabStartScrollX = -1;
    var isTabMoving = false;
    var momentumScrollTimer = null;
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
    
    var lastScrollPosition = null;
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
        
                updateTimer = window.setTimeout(updateList,15000);
            }
            else 
            {
                try 
                {
                    window.top.mx.State.handleRequestError(this.status,url,updateList);
                }
                catch
                {
                    updateTimer = window.setTimeout(updateList, 60000);
                }
            }
        };
        
        var data = {};
        data['count'] = containers.length;
        data['sub'] = folder;
        
        xhr.send(JSON.stringify(data));
    }
    
    updateList();
</script>
</body>
</html>
