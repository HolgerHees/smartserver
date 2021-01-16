mx.Swipe = (function( ret ) {
    var supportTouch;
    var touchStartEvent;
    var touchEndEvent;
    var touchMoveEvent;
    var touchCancelEvent;
    var scrollEvent;

    var currentTarget;
    var lastX;
    var lastY;
    var startX;
    var startY;
    var posHistory;

    var swipeActive = false;
    var clickAttached = false;

    function click(event)
    {
        event.preventDefault();
        event.stopPropagation();

        //console.log("prevent click");
    }

    function touchEnd(event)
    {
        swipeActive = false;

        window.removeEventListener(touchMoveEvent,touchMove);
        window.removeEventListener(touchEndEvent,touchEnd);
        window.removeEventListener(touchCancelEvent,touchEnd);

        if( clickAttached )
        {
            if (event === null)
            {
                //console.log("touchEndForced");
                currentTarget.removeEventListener("click", click);
            }
            else
            {
                //console.log("touchEndPre");
                // Remove click event handler with a small delay. Because click event is triggered after the touchEnd event.
                window.setTimeout(function()
                {
                    //console.log("touchEndPost");
                    //if( this !== currentTarget )
                    //{
                    //    console.log("touchEndFixed !!!!!!!!!!!!!!!!!");
                    //}

                    this.removeEventListener("click", click);

                }.bind(currentTarget), 100);

                // we have to use bind, otherwise if another touch event happens during this timeout period it will overwrite the currentTarget
            }

            clickAttached = false;
        }
        //else
        //{
            //console.log("touchEnd");
        //}

        var posEntry = posHistory[ posHistory.length - 1 ];
        var lastTime = posEntry.time;
        lastX = posEntry.clientX;
        lastY = posEntry.clientY;

        var accelerationX = 0;
        var accelerationY = 0;
        for( var i = posHistory.length - 1; i >= 0 ; i-- )
        {
            var posEntry = posHistory[i];
            var accelerationTime = lastTime - posEntry.time;
            if( accelerationTime >= 100 || i === 0 )
            {
                accelerationX = ( lastX - posEntry.clientX ) / accelerationTime;
                accelerationY = ( lastY - posEntry.clientY ) / accelerationTime;
                break;
            }
        }

        mx.Core.triggerEvent(currentTarget, 'tapend', true, { accelerationX: accelerationX, accelerationY: accelerationY } );
    };

    function touchMove(event)
    {
        var touchEvent = mx.Core.getEvent(event);

        var diffX = Math.abs( startX - touchEvent.clientX );
        var diffY = Math.abs( startY - touchEvent.clientY );

        if( diffX < 10 && diffY < 10 ) return;

        if( !clickAttached )
        {
            //console.log("touchMove");
            // prevent triggering click events
            //document.addEventListener("click",click);
            currentTarget.addEventListener("click", click);
            clickAttached = true;
        }

        mx.Core.triggerEvent(currentTarget, 'tapmove', true, { clientX: touchEvent.clientX, clientY: touchEvent.clientY, diffX: lastX - touchEvent.clientX, diffY: lastY - touchEvent.clientY } );

        lastX = touchEvent.clientX;
        lastY= touchEvent.clientY;

        posHistory.push({clientX: lastX, clientY: lastY, time: Date.now()});
    };

    function touchStart(event)
    {
        if ( event.which && event.which !== 1 ) {
            return false;
        }

        // we missed a touchEnd event so we have to simulate it
        if( swipeActive ) touchEnd(null);

        swipeActive = true;

        //console.log("touchStart");
        
        var touchEvent = mx.Core.getEvent(event);
        currentTarget = touchEvent.target;

        startX = lastX = touchEvent.clientX;
        startY = lastY = touchEvent.clientY;

        posHistory = [{clientX: startX, clientY: startY, time: Date.now()}];

        window.addEventListener(touchMoveEvent,touchMove);
        window.addEventListener(touchEndEvent,touchEnd);
        window.addEventListener(touchCancelEvent,touchEnd);

        // IE does not handle window leave events. A workaround is to catch body leave events
        if( mx.Core.isIEorEdge() ) mx.$("body").addEventListener("mouseleave", touchEnd);

        mx.Core.triggerEvent(currentTarget, 'tapstart', true, {clientX: startX, clientY: startY} );
    };

    ret.init = function()
    {
        supportTouch = mx.Core.isTouchDevice();
        touchStartEvent = supportTouch ? "touchstart" : "mousedown";
        touchEndEvent = supportTouch ? "touchend" : "mouseup";
        touchMoveEvent = supportTouch ? "touchmove" : "mousemove";
        touchCancelEvent = supportTouch ? "touchcancel" : "mousecancel";
        scrollEvent = "touchmove scroll";

        window.addEventListener(touchStartEvent, touchStart);

        /*window.addEventListener(scrollEvent,function(e)
        {
            console.log("scrollEvent");
        });*/
    };

    return ret;
})( mx.Swipe || {} );
