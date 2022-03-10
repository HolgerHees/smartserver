mx.State = (function( ret ) {
    ret.SUSPEND = -1;
    ret.OFFLINE = 0;
    ret.ONLINE = 1;
    ret.UNREACHABLE = 2;
    ret.REACHABLE = 3;
    ret.UNAUTHORIZED = 4;
    ret.AUTHORIZED = 5;

    var connectionState = ret.AUTHORIZED;
    var isVisible = true;
    
    var reachabilityTimer = false;
    
    var connectionStateCallbacks = [];
    
    var connectionChangedCallback = false;
    
    var checkInProgress = false;
    
    var debug = true;
        
    function setConnectionState(state)
    {
        if( connectionState != state )
        {
            connectionState = state;
            if( isVisible ) connectionChangedCallback(connectionState,true);
        }
        
        if( typeof connectionStateCallbacks[connectionState] != "undefined" && connectionStateCallbacks[connectionState].length > 0 ) 
        {
            var callbacks = connectionStateCallbacks[connectionState];
            connectionStateCallbacks[connectionState] = [];
            for( i = 0; i < callbacks.length; i++ )
            {
                callbacks[i]();
            }
        }
    }
    
    function clearTimer()
    {
        if( reachabilityTimer )
        {
            window.clearTimeout(reachabilityTimer);
            reachabilityTimer = false;
        }
    }
    
    function showLoginDialog()
    {
        if( confirm( mx.I18N.get("Authentication failed. Please try again.") + ( status ? "\n(" + status + ")" : "" ) ) )
        {
            window.location.reload();
        }
    }
    
    function getUrl(url,callback)
    {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", url);
        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {        
            if( this.readyState != 4 ) return;
            callback(this);
        };
        xhr.send();
    }

    function checkReachability(showProgress)
    {       
        if( connectionState == mx.State.OFFLINE )
        {
            if( debug ) console.log("mx.Status.checkReachability: callback suspended => offline");
        }
        else if( !checkInProgress )
        {
            checkInProgress = true;
            if( showProgress ) progressCallback(true);
            
            if( debug ) console.log("mx.Status.checkReachability: check reachability");

            var id = Math.round( Date.now() / 1000 );
            var reachabilityCheckUrl = '//' + mx.Host.getAuthSubDomain() + mx.Host.getDomain() + '/main/manifest.json?id='+id;
            getUrl(reachabilityCheckUrl,function(rc_response)
            {
                if( debug ) console.log("mx.Status.checkReachability: reachability response code " + rc_response.status);

                if( rc_response.status == 200 )
                {
                    if( debug ) console.log("mx.Status.checkReachability: is reachable");
                    setConnectionState(mx.State.REACHABLE);
                    
                    if( debug ) console.log("mx.Status.checkReachability: check authorization");
                    var authorizedCheckUrl = '//' + mx.Host.getAuthSubDomain() + mx.Host.getDomain();
                    getUrl(authorizedCheckUrl,function(ac_response)
                    {
                        if( debug ) console.log("mx.Status.checkReachability: authorization response code " + ac_response.status);

                        if( ac_response.status == 200 )
                        {
                            if( debug ) console.log("mx.Status.checkReachability: is authorized");
                            setConnectionState(mx.State.AUTHORIZED);
                        }
                        else
                        { 
                            if( debug ) console.log("mx.Status.checkReachability: is unauthorized");
                            setConnectionState(mx.State.UNAUTHORIZED);
                            
                            if( isVisible )
                            {
                                if( debug ) console.log("mx.Status.checkReachability: relogin");
                                showLoginDialog();
                            }
                            else
                            {
                                if( debug ) console.log("mx.Status.checkReachability: callback suspended => no relogin possible => not visible");
                            }
                        }

                        checkInProgress = false;
                        if( showProgress ) progressCallback(false);
                    });
                }
                else
                {
                    if( debug ) console.log("mx.Status.checkReachability: unreachable");
                    setConnectionState(mx.State.UNREACHABLE);
                    
                    reachabilityTimer = window.setTimeout(function(){ 
                        reachabilityTimer = false;
                        checkReachability(false); 
                    },2000);

                    checkInProgress = false;
                    if( showProgress ) progressCallback(false);
                }
            });
            
        }
    }
    
    ret.handleRequestError = function(status,url,callback,timeout)
    {
        if( debug ) console.log("mx.Status.handleRequestError: status => " + status + ", url => " + url);
        
        if( status == 404 )
        {
            if( debug ) console.error("Skipped state check for 404");
        }
        else if( status >= 500 )
        {
            return window.setTimeout(callback, timeout ? timeout : 15000);
        }
        /*else if( ( this.status == 401 || this.status == 403 ) && connectionState >= mx.State.REACHABLE && isVisible )
        {
            if( debug ) console.log("mx.Status.handleRequestError: unauthorized");
            setConnectionState(mx.State.UNAUTHORIZED);

            if( debug ) console.log("mx.Status.handleRequestError: relogin");
            showLoginDialog();
        }*/
        else
        {
            connectionStateCallbacks[mx.State.AUTHORIZED].push( callback );

            if( isVisible ) 
            {
                clearTimer();
                checkReachability(false);
            }
            else if( connectionState > mx.State.UNREACHABLE )
            {
                if( debug ) console.log("mx.Status.handleRequestError: unreachable");
                setConnectionState(mx.State.UNREACHABLE);
            }
        }
    };
    
    // https://developers.google.com/web/updates/2018/07/page-lifecycle-api
    ret.init = function(_connectionChangedCallback,_progressCallback)
    {
        connectionChangedCallback = _connectionChangedCallback;
        progressCallback = _progressCallback;
        
        connectionStateCallbacks = {}
        connectionStateCallbacks[mx.State.AUTHORIZED] = [];
        
        function handleState( _isVisible, animated )
        {
            isVisible = _isVisible;
            
            if( isVisible )
            {
                connectionChangedCallback(connectionState,false);
                window.removeEventListener("mousedown", handleVisibilityFallback);

                if( connectionState < mx.State.AUTHORIZED )
                {
                    clearTimer();
                    checkReachability(true);
                }
            }
            else
            {
                connectionChangedCallback(mx.State.SUSPEND,true);
                window.addEventListener("mousedown", handleVisibilityFallback);
                clearTimer();
            }
        }
        
        function handleVisibilityFallback()
        {
            if( !isVisible )
            {
                if( debug ) console.log("mx.Status.handleVisibilityFallback: true");

                handleState(true, true);
            }
        }

        document.addEventListener("visibilitychange", function()
        {
            if( debug ) console.log("mx.Status.handleVisibilityChange: " + !document['hidden']);

            handleState( !document['hidden'], false );
        }, false);

        window.addEventListener("offline", function(e) {
            if( debug ) console.log("mx.State: changed to offline");
            setConnectionState(mx.State.OFFLINE);

            clearTimer();
        });

        window.addEventListener("online", function(e) {
            if( debug ) console.log("mx.State: changed to online");
            setConnectionState(mx.State.ONLINE);
            
            if( isVisible ) 
            {
                clearTimer();
                checkReachability(true);
            }
        });
    };
        
    return ret;
})( mx.State || {} );
