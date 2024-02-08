mx.ServiceSocket = (function( ret ) {
    ret.init = function(service_name)
    {
        var initialized = true;
        var errorCallback = null;

        function onError(err)
        {
            if( !initialized ) return;

            if( !errorCallback ) mx.Error.handleError( mx.I18N.get( "Service is currently not available") );
            else errorCallback(err);
        }

        function onConnect()
        {
            if( !initialized ) return;

            if( !errorCallback ) mx.Error.confirmSuccess();
        }

        var socket = io("/", {path: '/' + service_name + '/api/socket.io' });
        socket.on('connect_error', err => onError(err));
        socket.on('connect_failed', err => onError(err));
        socket.on('disconnect', err => onError(err));
        socket.on('connect', err => onConnect());

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
