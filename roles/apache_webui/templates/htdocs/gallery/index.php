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
    include "config.php";
    
    if( empty($_GET["sub"]) )
    {
        exit;
    }
    $sub_folder = $_GET['sub'];
    
    class CameraImage {
        private $ftp_folder = null;
        private $sub_folder = null;
        private $file = null;
        private $time = null;
        
        function __construct($ftp_folder , $sub_folder, $file, $creation_time ) {
            $this->ftp_folder = $ftp_folder;
            $this->sub_folder = $sub_folder;
            $this->file = $file;
            
            $this->time = $creation_time;
        }
        
        function getFile()
        {
            return $this->file;
        }
        
        function getPath()
        {
            return $this->ftp_folder . $this->sub_folder . "/" . $this->file;
        }
        
        function getTime()
        {
            return $this->time;
        }
    }
    
    $file_times = array();
    $list = shell_exec("stat -c \"%y %n\" " . $ftp_folder . $sub_folder . "/*");
    foreach( explode("\n",$list) as $line )
    {
        if( empty($line) ) continue;
        
        $parts = explode(" ",$line);
        
        $time = strtotime($parts[0] . " " . $parts[1] . " " . $parts[2]);
        $time = DateTime::createFromFormat('Y-m-d H:i:s O', $parts[0] . " " . explode(".",$parts[1])[0] . " " . $parts[2]);
        $file_times[$parts[3]] = $time;
    }
    
    $files = scandir($ftp_folder . $sub_folder);
    $images = [];
    foreach( $files as $file )
    {
        if( $file == '.' or $file == '..' || is_dir($sub_folder.$file) ) continue;
        $images[] = new CameraImage($ftp_folder , $sub_folder, $file, $file_times[ $ftp_folder . $sub_folder . "/" . $file ] );;
    }
    usort($images,function($a,$b){ return $a->getTime()->getTimestamp() < $b->getTime()->getTimestamp(); });
    
    list($width, $height, $type, $attr) = getimagesize($images[0]->getPath());
    
    $starttime = $images[0]->getTime();
    $starttime->setTime($starttime->format('H'),0,0,0);
    $starttime->add(new DateInterval('PT1H'));

    $endtime = $images[count($images)-1]->getTime();
    $endtime->setTime($endtime->format('H'),0,0,0);

    $_diff = $starttime->diff($endtime);
    $_hours = $_diff->h;
    $_hours = $_hours + ($_diff->days*24);
    $_max_steps = 100;
    $stepDurationInHours = ceil($_hours / $_max_steps);
    $stepSizeInPercent = $stepDurationInHours * $_max_steps / $_hours;
    
    $grouped_images = array();
    $currenttime = clone $starttime;
    while( $currenttime->getTimestamp() >= $endtime->getTimestamp() )
    {
        $grouped_images[$currenttime->getTimestamp()] = array();
        $currenttime->sub(new DateInterval('PT'.$stepDurationInHours.'H'));
    }
    
    foreach( $images as $image ){
        $current_step_time = clone $image->getTime();
        $current_step_time->setTime($current_step_time->format('H'),0,0,0);
        
        //if( !isset($grouped_images[$current_step_time->getTimestamp()]) )
        //{
        //    echo "missing " . $current_step_time->format("d.m H:i:s") . "\n";
        //}
        
        array_push($grouped_images[$current_step_time->getTimestamp()],$image);
    }
?>
<div class="tooltip"><span class="text"></span><span class="arrow"></span></div>
<div class="stepline-scrollarea-wrapper">
<?php
    $max_count = 0;
    foreach( $grouped_images as $key => $value )
    {
        if( $max_count < count($value) ) $max_count = count($value);
    }
    
    $lastLabledDate = NULL;
    $lastLabledTime = NULL;
    foreach( $grouped_images as $key => $values )
    {
        $time = new DateTime();
        $time->setTimestamp($key);
            
        echo "<div class='slot";
        
        if( count($values) > 0 )
        {
            echo " filled' onclick='jumpToSlot(" . $key . ")";
        }
        
        if( count($values) > 0 )
        {
            echo "' data-formattedtime='" . $time->format('d.m. H:i') . "' data-count='" . count($values);
        }
        
        echo "' data-timeslot='" . $key . "'>";
        
        if( $lastLabledDate == NULL || $lastLabledDate->format("d") != $time->format("d") )
        {
            echo "<div class='date'>" . $time->format('d.m.') . "</div>";
            $lastLabledDate = $time;
        }

        if( $lastLabledTime == NULL || $lastLabledTime->getTimestamp() - $key > (60*60*12) )
        {   
            $time = new DateTime();
            $time->setTimestamp($key);
            
            echo "<div class='time'>" . $time->format('H:i') . "</div>";
            $lastLabledTime = $time;
        }

        if( count($values) > 0 )
        {
            echo "<div class='bar' style='height:" . ceil( count($values) * 100 / $max_count ) . "%'></div>";
        }
        else
        {
            echo "<div class='bar' style='height:0'></div>";
        }
        
        //if( 
        
        echo "</div>";
    }
?>
</div>

<div id="gallery">
  <div class="layer"></div>
  <span class="button previous icon-left" onclick="jumpToPreviousImage()"></span>
  <span class="button next icon-right" onclick="jumpToNextImage()"></span>
  <span class="button close icon-cancel" onclick="closeDetails()"></span>
<?php
    foreach( $images as $index => $image )
    {
        // add timeslot key
        // add formatted time
        
        $date = clone $image->getTime();
        $formattedTime = $date->format("d.m. H:i:s");
        
        $date->setTime( $date->format("H"), 0, 0, 0 );
        
        
        echo "<div class='container' data-index='" . $index . "' onclick='openDetails(" . $index . ")' data-src='" . urlencode($image->getFile()) . "' data-formattedtime='" . $formattedTime . "' data-timeslot='" . $date->getTimestamp() . "'><div class='dummy'></div></div>";
    }
?>
</div>
<script> 
    var isFullscreen = false;
    var activeItem = null;
    var activeSlot = null;
    var imageHeight = <?php echo $height; ?>;
    var imageWidth = <?php echo $width; ?>;
    var folder = '<?php echo $sub_folder; ?>';
    var requestedScrollPosition = null;
    var debug = true;
    
    var slotOverview = document.querySelector(".stepline-scrollarea-wrapper");

    var tooltip = document.querySelector(".tooltip");
    var tooltipArrow = tooltip.querySelector(".arrow");
    
    var gallery = document.querySelector("#gallery");
    var galleryPreviousButton = gallery.querySelector(".button.previous");
    var galleryNextButton = gallery.querySelector(".button.next");
            
    var style = document.createElement('style');
    style.type = 'text/css';
    style.innerHTML = 'div.dummy { margin-top: ' + (imageHeight*100/imageWidth) + '%; }';
    document.getElementsByTagName('head')[0].appendChild(style);
    
    var style = document.createElement('style');
    style.type = 'text/css';
    style.innerHTML = '.stepline-scrollarea-wrapper > div.slot { width: <?php echo $stepSizeInPercent; ?>%; }';
    document.getElementsByTagName('head')[0].appendChild(style);

    var galleryRect = gallery.getBoundingClientRect();
    
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

    var containers = document.querySelectorAll(".container");
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

    var slotTooltipElement = null;
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
</script>
</body>
</html>
