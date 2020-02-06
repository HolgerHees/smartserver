mx.Host = (function( ret ) {
    var host = location.host;
    var parts = host.split(".");
    var authType = false;
    if( parts.length == 3 )
    {
        var subDomain = parts.shift();
        if( subDomain.indexOf("fa") === 0 ) authType = "fa";
        else if( subDomain.indexOf("ba") === 0 ) authType = "ba";
    }
    var domain = parts.join(".");
    
    var base = window.location.href;
    base = base.replace(document.location.protocol,"");
    base = base.substring(0,base.lastIndexOf("/")+1);


    ret.getAuthPrefix = function()
    {
        return authType ? authType + '-' : "";
    };

    ret.getAuthSubDomain = function()
    {
        return authType ? authType + '.' : "";
    };

    ret.getDomain = function()
    {
        return domain;
    };
    
    ret.getBase = function()
    {
        return base;
    };
    
    ret.getParameter = function(name) {

        var str = window.location.search;
        var params = {};

        str.replace(
            new RegExp( "([^?=&]+)(=([^&]*))?", "g" ),
            function( $0, $1, $2, $3 ){
                params[ $1 ] = $3;
            }
        );
        return typeof name != "undefined" ? params[name] : params;
    };
    
    return ret;
})( mx.Host || {} );
