mx.Logfile = (function( ret ) {
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
    /*var lastHashScrollY = 0;
    
    window.addEventListener("hashchange", function(e) {
      if( lastHashScrollY == -1 ) return;
      window.scrollTo(0,lastHashScrollY);
    },false);*/

    function enableBottomScroll()
    {
        var scrollControl = document.querySelector(".scrollControl");
        scrollControl.classList.add("active");
        mx.Logfile.goToBottom();
        window.setTimeout(function()
        {
            bottomScrollEnabled = true;
        },500);
    }

    function disableBottomScroll()
    {
        var scrollControl = document.querySelector(".scrollControl");
        scrollControl.classList.remove("active");
        bottomScrollEnabled = false;
    }
    
    function refreshDuration()
    {
        formattedDuration = mx.Logfile.formatDuration(++duration);
        
        runtimeElement.innerHTML = formattedDuration;
    }
    
    function handleDetailUpdates(data)
    {
        var content = document.createElement("div");
        content.innerHTML = data;

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
            var startIndex = 0;
            if( logElement.lastChild )
            {
                logElement.lastChild.innerHTML = logElement.lastChild.innerHTML + _logElements[0].innerHTML;
                startIndex = 1;
            }
            
            for( i = startIndex; i < _logElements.length; i++ )
            {
                logElement.appendChild(_logElements[i].cloneNode(true));
            }

            if( bottomScrollEnabled ) mx.Logfile.goToBottom();
        }
        
        var stateRawElement = content.querySelector("#state");
        if( stateRawElement.innerHTML == 'running' )
        {
            return true;
        }
        else
        {
            stateColorElement.classList.remove('running');
            stateColorElement.classList.add(stateRawElement.innerHTML);
            return false;
        }        
    }
    
    function updateDetails(force)
    {
        var refreshInterval = bottomScrollEnabled ? 2 : 10;
        
        if( force ) currentInterval = 0;
        
        if( currentInterval == 0 )
        {
            var url = mx.Host.getBase() + 'details_update.php' + window.location.search + '&position=' + currentPosition;
            
            var xhr = new XMLHttpRequest();
            xhr.open("GET", url );
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                    var isRunning = handleDetailUpdates(this.response);
                    
                    if( isRunning )
                    {
                        updateTimer = window.setTimeout(updateDetails,1000);
                    }
                    else
                    {
                        updateTimer = false;
                    }        
                }
                else 
                {
                    try 
                    {
                        window.top.mx.State.handleRequestError(this.status,url,updateDetails);
                    }
                    catch
                    {
                        updateTimer = window.setTimeout(updateDetails,5000);
                    }
                }
            };
            xhr.send();
        }
        else if( updateTimer )
        {
            refreshDuration();
            updateTimer = window.setTimeout(updateDetails,1000);
        }

        currentInterval += 1;
        if( currentInterval == refreshInterval ) currentInterval = 0;
    } 

    ret.goToBottom = function()
    {
        window.scrollTo(0,document.body.scrollHeight + 100);
        logElement.scrollLeft = 0;
    }
    
    ret.goToTop = function()
    {
        window.scrollTo(0,0);
        logElement.scrollLeft = 0;
        if( bottomScrollEnabled ) mx.Logfile.toggleBottomScroll();
    }
    
    ret.toggleBottomScroll = function()
    {
        if( !bottomScrollEnabled )
        {
            //lastHashScrollY = -1;
            
            enableBottomScroll();
            
            if( updateTimer )
            {
                window.clearTimeout(updateTimer);
                updateTimer = false;
                updateDetails(true);
            }
            
            location.hash = '#autoscroll';
        }
        else
        {
            //lastHashScrollY = window.scrollY;
        
            disableBottomScroll();

            location.hash = location.hash.replace('#autoscroll','_');
        }
    }

    ret.checkScrollPosition = function(e,body,goToControl,logLayerScrolled)
    {
        if( bottomScrollEnabled )
        {
            if( ( logLayerScrolled && logElement.scrollLeft > 0 ) || ( !logLayerScrolled && lastScrollY > window.scrollY + 30 ) )
            {
                mx.Logfile.toggleBottomScroll();
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
                if( goToControl.classList.contains("singleButton") )
                {
                    goToControl.firstChild.classList.remove("icon-down-1")
                }
                else
                {
                    goToControl.style.opacity = "";
                }

                goToControl.setAttribute("onClick", "mx.Logfile.goToTop()");
                goToControl.firstChild.classList.add("icon-up")
            }
            else
            {
                body.classList.remove('sticky');
                if( goToControl.classList.contains("singleButton") )
                {
                    goToControl.setAttribute("onClick", "mx.Logfile.goToBottom()");
                    goToControl.firstChild.classList.add("icon-down-1")
                    goToControl.firstChild.classList.remove("icon-up")
                }
                else
                {
                    goToControl.style.opacity = "0";
                    goToControl.setAttribute("onClick", "");
                }
            }
        }
    }
        
    ret.formatDuration = function(duration)
    {
        var days = Math.floor(duration / 86400);
        duration -= days * 86400;
        var hours = Math.floor(duration / 3600);
        duration -= hours * 3600;
        var minutes = Math.floor(duration / 60);
        var seconds = duration - minutes * 60;
        
        if( hours < 10 ) hours = '0' + hours;
        if( minutes < 10 ) minutes = '0' + minutes;
        if( seconds < 10 ) seconds = '0' + seconds;

        return hours + ':' + minutes + ':' + seconds;
    }

    ret.startUpdateProcess = function(position)
    {
        if( location.hash == '#autoscroll' )
        {
            enableBottomScroll();
        }
        
        currentPosition = position;
        updateDetails(true);
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
})( mx.Logfile || {} );
