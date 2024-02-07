mx.ServiceSocket = (function( ret ) {
    ret.init = function(service_name)
    {
        var errorCallback = null;

        function onError(err)
        {
            if( !errorCallback ) mx.Error.handleErrors( mx.I18N.get( "Service is currently not available") );
            else errorCallback(err);
        }

        function onConnect()
        {
            if( !errorCallback ) mx.Error.confirmSuccess();
        }

        var socket = io("/", {path: '/' + service_name + '/api/socket.io' });
        socket.on('connect_error', err => onError(err));
        socket.on('connect_failed', err => onError(err));
        socket.on('disconnect', err => onError(err));
        socket.on('connect', err => onConnect());

        var _on = socket.on.bind(socket);
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
