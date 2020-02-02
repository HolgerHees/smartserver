mx.CIDetails = (function( ret ) {
    var stateColorElement = null;
    var stateTextElement = null;
    var runtimeElement = null;
    var logElement = null;

    var duration = 0;
    var currentPosition = 0;

    var currentInterval = 0;
    var bottomScrollEnabled = false;

    var updateTimer = false;

    var lastScrollY = 0;
    var lastHashScrollY = 0;
    
    window.addEventListener("hashchange", function(e) {
      if( lastHashScrollY == -1 ) return;
      window.scrollTo(0,lastHashScrollY);
    },false);

    function enableBottomScroll()
    {
        var scrollControl = document.querySelector(".scrollControl");
        scrollControl.classList.add("active");
        bottomScrollEnabled = true;
        goToBottom();
    }

    function disableBottomScroll()
    {
        var scrollControl = document.querySelector(".scrollControl");
        scrollControl.classList.remove("active");
        bottomScrollEnabled = false;
    }
    
    function goToBottom()
    {
        window.scrollTo(0,document.body.scrollHeight);
        logElement.scrollLeft = 0;
    }
    
    function refreshDuration()
    {
        formattedDuration = mx.CICore.formatDuration(++duration);
        
        runtimeElement.innerHTML = formattedDuration;
    }
    
    ret.goToTop = function()
    {
        window.scrollTo(0,0);
        logElement.scrollLeft = 0;
        if( bottomScrollEnabled ) mx.CIDetails.toggleBottomScroll();
    }
    
    ret.toggleBottomScroll = function()
    {
        if( !bottomScrollEnabled )
        {
            lastHashScrollY = -1;
            
            enableBottomScroll();
            
            if( updateTimer )
            {
                window.clearTimeout(updateTimer);
                updateTimer = false;
                mx.CIDetails.updateDetails(true);
            }
            
            location.hash = '#autoscroll';
        }
        else
        {
            lastHashScrollY = window.scrollY;
        
            disableBottomScroll();

            location.hash = location.hash.replace('#autoscroll','');
        }
    }

    ret.checkScrollPosition = function(e,body,goToTopControl,logLayerScrolled)
    {
        if( bottomScrollEnabled )
        {
            if( ( logLayerScrolled && logElement.scrollLeft > 0 ) || ( !logLayerScrolled && lastScrollY > window.scrollY + 30 ) )
            {
                mx.CIDetails.toggleBottomScroll();
            }
        }
        
        if( !logLayerScrolled )
        {
            if( window.scrollY > lastScrollY )
            {
                lastScrollY = window.scrollY;
            }
            
            if( window.scrollY > 0 )
            {
                body.classList.add('sticky');
                goToTopControl.style.opacity = "";
            }
            else
            {
                body.classList.remove('sticky');
                goToTopControl.style.opacity = "0";
            }
        }
    }
    
    ret.updateDetails = function(force)
    {
        var refreshInterval = bottomScrollEnabled ? 2 : 10;
        
        if( force ) currentInterval = 0;
        
        if( currentInterval == 0 )
        {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", 'details_update.php' + window.location.search + '&position=' + currentPosition );
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                    var content = document.createElement("div");
                    content.innerHTML = this.response;
                    
                    currentPosition = parseInt(content.querySelector("#currentPosition").innerHTML);
                    duration = parseInt(content.querySelector("#duration").innerHTML);
                    
                    runtimeElement.innerHTML = content.querySelector("#durationFormatted").innerHTML;
                    
                    var _stateElement = content.querySelector("#stateFormatted");
                    if( stateTextElement.innerHTML != _stateElement.firstChild.innerHTML )
                    {
                        stateTextElement.innerHTML = _stateElement.firstChild.innerHTML;
                        stateTextElement.className = _stateElement.firstChild.className;
                    }
                    
                    var _logElements = content.querySelector("#logs").childNodes;
                    if( _logElements.length > 0 )
                    {
                        logElement.lastChild.innerHTML = logElement.lastChild.innerHTML + _logElements[0].innerHTML;
                        
                        for( i = 1; i < _logElements.length; i++ )
                        {
                            logElement.appendChild(_logElements[i].cloneNode(true));
                        }

                        if( bottomScrollEnabled ) goToBottom();
                    }
                    
                    var stateRawElement = content.querySelector("#state");
                    if( stateRawElement.innerHTML == 'running' )
                    {
                        updateTimer = window.setTimeout(mx.CIDetails.updateDetails,1000);
                    }
                    else
                    {
                        stateColorElement.classList.remove('running');
                        stateColorElement.classList.add(stateRawElement.innerHTML);
                        updateTimer = false;
                    }
                }
                else 
                {
                    alert("was not able to download '" + 'details_update.php?' + window.location.search + "'");
                }
            };
            xhr.send();
        }
        else if( updateTimer )
        {
            refreshDuration();
            updateTimer = window.setTimeout(mx.CIDetails.updateDetails,1000);
        }

        currentInterval += 1;
        if( currentInterval == refreshInterval ) currentInterval = 0;
    } 
    
    ret.startUpdateProcess = function(position)
    {
        if( location.hash == '#autoscroll' )
        {
            enableBottomScroll();
        }
        
        currentPosition = position;
        mx.CIDetails.updateDetails(true);
    }
    
    ret.init = function(_duration, _stateColorElement, _stateTextElement, _runtimeElement, _logElement)
    {
        duration = _duration;
        stateColorElement = _stateColorElement;
        stateTextElement = _stateTextElement;
        runtimeElement = _runtimeElement;
        logElement = _logElement;
    }

    return ret;
})( mx.CIDetails || {} );
