mx.ServiceSocket = (function( ret ) {
    ret.init = function(service_name)
    {
        var initialized = true;
        var errorCallback = null;

        window.addEventListener("beforeunload", (event) => { initialized = false; });

        function onError(err)
        {
            if( !initialized ) return;

            if( !errorCallback ) mx.Error.handleError( mx.I18N.get( "Service is currently not available") );
            else errorCallback(err);
        }

        function onDisconnect(err)
        {
            if( !initialized ) return;

            onError(err);
        }

        function onConnect(data)
        {
            if( !initialized ) return;

            if( !errorCallback ) mx.Error.confirmSuccess();
        }

        function onStatus(status)
        {
            if( status["code"] == 0 ) console.info(status["message"]);
            else console.error(status["message"]);
        }

        var socket = io("/", {path: '/' + service_name + '/api/socket.io', transports: ["polling", "websocket"] });
        socket.on('connect_error', onError );
        socket.on('connect_failed', onError);
        socket.on('disconnect', onDisconnect );
        socket.on('connect', onConnect );
        socket.on('status', onStatus );

        var _on = socket.on.bind(socket);
        var _close = socket.close.bind(socket);
        socket.close = function()
        {
            initialized = false;
            _close();
        }
        socket.on = function(topic, callback) {
            if( topic == "error" )
            {
                errorCallback = callback;
            }
            else
            {
                _on(topic, callback );
            }
        }
        return socket;
    }
    return ret
})( mx.ServiceSocket || {} );
