mx.Host = (function( ret ) {
    var host = location.host;
    var parts = host.split(".");
    var authType = "";
    if( parts.length == 3 )
    {
        var subDomain = parts.shift();
        if( subDomain.indexOf("fa") === 0 ) authType = "fa_";
        else if( subDomain.indexOf("ba") === 0 ) authType = "ba_";
    }
    var domain = parts.join(".");

    ret.getAuthType = function()
    {
        return authType;
    }

    ret.getDomain = function()
    {
        return domain;
    }
    
    ret.forceLogin = function(status)
    {
        if( confirm( mx.I18N.get("Authentication failed. Please try again." + ( status ? "\n(" + status + ")" : "" ) ) ) )
        {
            window.location.reload();
        }
    }

    return ret;
})( mx.Host || {} );
