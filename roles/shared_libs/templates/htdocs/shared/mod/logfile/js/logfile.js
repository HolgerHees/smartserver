mx.Logfile = (function( ret ) {
    var logElement;
    var scrollControlElement;
    var goToControlElement;
    var runtimeControlElement = null;

    var bottomScrollEnabled = false;
    var lastScrollY = 0;

    function enableBottomScroll()
    {
        scrollControlElement.classList.add("active");
        mx.Logfile.goToBottom();
        window.setTimeout(function()
        {
            bottomScrollEnabled = true;
        },500);
    }

    function disableBottomScroll()
    {
        scrollControlElement.classList.remove("active");
        bottomScrollEnabled = false;
    }

    function refreshDuration()
    {
        formattedDuration = mx.Logfile.formatDuration(++duration);

        runtimeElement.innerHTML = formattedDuration;
    }

    ret.triggerUpdate = function()
    {
        if( bottomScrollEnabled ) mx.Logfile.goToBottom();
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
        if( !bottomScrollEnabled ) enableBottomScroll();
        else disableBottomScroll();
    }

    ret.checkScrollPosition = function(e,logLayerScrolled)
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
                document.body.classList.add('sticky');
                if( goToControlElement.classList.contains("singleButton") )
                {
                    goToControlElement.firstChild.classList.remove("icon-down-1")
                }

                goToControlElement.setAttribute("onClick", "mx.Logfile.goToTop()");
                goToControlElement.firstChild.classList.add("icon-up")
                goToControlElement.classList.add("enabled");
            }
            else
            {
                document.body.classList.remove('sticky');
                if( goToControlElement.classList.contains("singleButton") && logElement.scrollHeight + logElement.offsetTop > document.body.clientHeight )
                {
                    goToControlElement.setAttribute("onClick", "mx.Logfile.goToBottom()");
                    goToControlElement.firstChild.classList.add("icon-down-1")
                    goToControlElement.firstChild.classList.remove("icon-up")
                    goToControlElement.classList.add("enabled");
                }
                else
                {
                    goToControlElement.classList.remove("enabled");
                    goToControlElement.setAttribute("onClick", "");
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
        duration -= minutes * 60
        var seconds = Math.ceil(duration);

        if( hours < 10 ) hours = '0' + hours;
        if( minutes < 10 ) minutes = '0' + minutes;
        if( seconds < 10 ) seconds = '0' + seconds;

        return hours + ':' + minutes + ':' + seconds;
    }

    ret.getIcon = function(state)
    {
        switch( state )
        {
            case 'running':
                return '<span class="icon-dot"></span>';
            case 'success':
                return '<span class="icon-ok"></span>';
            case 'failed':
                return '<span class="icon-cancel"></span>';
            case 'crashed':
                return '<span class="icon-cancel"></span>';
            case 'retry':
                return '<span class="icon-ccw"></span>';
            case 'stopped':
                return '<span class="icon-block"></span>';
        }
    }

    ret.formatState = function(state)
    {
        return '<span class="text">' + state + '</span>' + mx.Logfile.getIcon(state);
    }

    ret.initData = function(startTime, duration, logs)
    {
        runtimeControlElement.innerHTML = mx.Logfile.formatDuration(duration);

        if( runtimeControlElement.dataset.state == "running" )
        {
            function counter()
            {
                let duration = Math.round( ( ( Date.now() - startTime.getTime() ) / 1000 ) );
                runtimeControlElement.innerHTML = mx.Logfile.formatDuration(duration);
                if( runtimeControlElement.dataset.state == "running" ) window.setTimeout(counter,1000);
            }
            counter();
            scrollControlElement.classList.add("enabled");
        }
        else
        {
            scrollControlElement.style.display = "none";
            goToControlElement.classList.add("singleButton");
        }

        logElement.innerHTML = logs.join("");

        logElement.addEventListener("scroll", function(e) {
            mx.Logfile.checkScrollPosition(e,true);
        },false);

        window.addEventListener("scroll",function(e)
        {
            mx.Logfile.checkScrollPosition(e,false);
        });

        mx.Logfile.checkScrollPosition(null,false);
    }

    ret.init = function(_logElement, _scrollControlElement, _goToControlElement, _runtimeControlElement)
    {
        logElement = _logElement;
        scrollControlElement = _scrollControlElement;
        goToControlElement = _goToControlElement;
        runtimeControlElement = _runtimeControlElement;
    }

    return ret;
})( mx.Logfile || {} );
