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

    ret.getAuthPrefix = function()
    {
        return authType ? authType + '_' : "";
    }

    ret.getAuthSubDomain = function()
    {
        return authType ? authType + '.' : "";
    }

    ret.getDomain = function()
    {
        return domain;
    }
    
    return ret;
})( mx.Host || {} );
