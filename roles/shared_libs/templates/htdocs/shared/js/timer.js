mx.Timer = (function( ret ) {
    var refreshTimer = [];

    ret.clean = function()
    {
        if(refreshTimer.length > 0 )
        {
            for( i = 0; i < refreshTimer.length; i++ )
            {
                window.clearTimeout(refreshTimer[i]);
            }
            refreshTimer=[];
        }
    };

    ret.stop = function(id)
    {
        refreshTimer.splice(refreshTimer.indexOf(id), 1);
        window.clearTimeout(id);
    }

    ret.register = function(func,timeout)
    {
        var refreshTimerID = window.setTimeout(function(){
            if( refreshTimer.includes( refreshTimerID) )
            { 
                refreshTimer.splice( refreshTimer.indexOf(refreshTimerID), 1 );
                func();
            }
        },timeout);
        refreshTimer.push( refreshTimerID );

        return refreshTimerID;
    };

    return ret;
})( mx.Timer || {} );
