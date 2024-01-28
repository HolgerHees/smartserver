mx.ServiceSocket = (function( ret ) {
    var socket = null;

    function handleErrors()
    {
        mx.Error.handleError( mx.I18N.get( "Service is currently not available") );
    }
    ret.on = function( topic, callback)
    {

    }
    ret.init = function( service_name)
    {
        socket = io("/", {path: '/' + service_name + '/api/socket.io' });
        socket.on('connect_error', err => handleErrors(err))
        socket.on('connect_failed', err => handleErrors(err))
        socket.on('disconnect', err => handleErrors(err))

        return {
            "on": function(topic, callback) {
                if( topic == "connect" )
                {
                    socket.on('connect', function() {
                        mx.Error.confirmSuccess();
                        callback(socket);
                    });
                }
                else
                {
                    socket.on(topic, callback );
                }
            }
        }
    }
    return ret
})( mx.ServiceSocket || {} );
