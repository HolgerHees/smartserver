mx.ServiceSocket = (function( ret ) {
    var sockets = {}
    var contexts = {}

    function wrapSocket(context, service_name, namespace, join_data_callback)
    {
        if( typeof(context.ServiceSocketUID) == 'undefined' )
        {
            context.ServiceSocketUID = Object.keys(contexts).length;
            contexts[context.ServiceSocketUID] = []
            context.addEventListener("beforeunload", function(){
                for( callback of contexts[context.ServiceSocketUID] ){ callback(); }
            });
        }

        var socket = sockets[service_name];

        var initialized = true;
        var error_triggered = false;
        var onError = null;
        var listener = [];
        var namespaces = new Set([]);

        var wrapper = {
            'triggerClose': function(msg)
            {
                initialized = false;
            },
            'triggerDisconnect': function(msg)
            {
                if( !initialized ) return;

                wrapper["triggerError"](msg);
            },
            'triggerError': function(msg)
            {
                if( !initialized ) return;

                if( !onError )
                {
                    error_triggered = true
                    mx.OnScriptReady.push(function(){ context.mx.Error.handleError( mx.I18N.get( "Service is currently not available") ) });
                }
                else onError(msg);
            },
            'triggerFailed': function(msg)
            {
                if( !initialized ) return;

                wrapper["triggerError"](msg);
            },
            'triggerConnect': function()
            {
                if( !initialized ) return;

                if( error_triggered )
                {
                    error_triggered = false;
                    mx.OnScriptReady.push(function(){ context.mx.Error.confirmSuccess() });
                }

                wrapper.emit('join', namespace, join_data_callback ? join_data_callback() : null);
            },
            'emit': function()
            {
                if( arguments[0] == "join" ) namespaces.add(arguments[1]);
                socket["socket"].emit(...arguments);
            },
            'close': function()
            {
                socket["socket"].close();
            },
            'on': function(topic, callback, _namespace=null)
            {
                if( topic == "error" )
                {
                    onError = callback;
                }
                else
                {
                    if( topic == "connect" )
                    {
                        if( socket["socket"].connected ) callback();
                    }
                    else
                    {
                        topic = ( _namespace ? _namespace : namespace ) + ":" + topic;
                    }

                    socket["socket"].on(topic, callback);
                    listener.push(callback);
                }
            }
        }

        contexts[context.ServiceSocketUID].push(function(){
            initialized = false;

            if( window == context ) return;

            for( callback of listener ){ socket["socket"].offAny(callback); }
            for( namespace of namespaces ){ wrapper.emit('leave', namespace); }

            let index = socket["wrapper"].indexOf(wrapper);
            socket["wrapper"].splice(index, 1);

            if( socket["wrapper"].length == 0 )
            {
                socket["socket"].close();
                delete sockets[service_name];
            }
        });
        if( socket["socket"].connected ) wrapper.triggerConnect();

        return wrapper;
    }

    ret.init = function(service_name, namespace, join_data_callback, context = null)
    {
        try
        {
            if( window.top != window && window.top.mx.ServiceSocket )
            {
                return window.top.mx.ServiceSocket.init(service_name, namespace, join_data_callback, window);
            }
        }
        catch (error){ console.error("Failed top window socketio check"); }

        if( sockets[service_name] )
        {
            let wrapper = wrapSocket(context ? context : window, service_name, namespace, join_data_callback);
            sockets[service_name]["wrapper"].push(wrapper);
            return wrapper;
        }

        //console.log("INIT ", context ? context : window, service_name);

        sockets[service_name] = {"socket": null, "wrapper": []};

        var socket = sockets[service_name]["socket"] = io("/", {path: '/' + service_name + '/api/socket.io', transports: ["websocket"] });
        var _close = socket.close.bind(socket);
        socket.close = function()
        {
            for( wrapper of sockets[service_name]["wrapper"] ){ wrapper.triggerClose(); }
            _close();
        }
        socket.on('connect', function(){ for( wrapper of sockets[service_name]["wrapper"] ){ wrapper.triggerConnect(); } });
        socket.on('disconnect', function(){ for( wrapper of sockets[service_name]["wrapper"] ){ wrapper.triggerDisconnect(); } });
        socket.on('connect_error', function(){ for( wrapper of sockets[service_name]["wrapper"] ){ wrapper.triggerError(); } });
        socket.on('connect_failed', function(){ for( wrapper of sockets[service_name]["wrapper"] ){ wrapper.triggerFailed(); } });
        socket.on('status', function(data)
        {
            if( status["code"] == 0 ) console.info(status["message"]);
            else console.error(status["message"]);
        });

        let wrapper = wrapSocket(context ? context : window, service_name, namespace, join_data_callback);
        sockets[service_name]["wrapper"].push(wrapper);
        return wrapper;
    }
    return ret
})( mx.ServiceSocket || {} );
