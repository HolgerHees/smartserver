mx.Panel = (function( ret ) {
    var _options = {
        topMargin: "0px",
        isSwipeable: false,
        isBackgroundLayerEnabled: false,
        maxBackgroundLayerOpacity: 0.5,
        selectors: {
            menuButtons: null,
            panelContainer: null,
            backgroundLayer: null
        },
        selectorsConfig : {
            asList: ['menuButtons']
        },
        classes: {
            main: "c-panel",
            type: "-is-position-left",
            animation: "-is-animated",
            open: "-is-open"
        }
    };

    var activeInstance = null;
    
    function enableBackgroundLayer(options,enabled)
    {
        options.isBackgroundLayerEnabled = enabled;
        if( options.isBackgroundLayerEnabled )
        {
            if( isOpen(options) )
            {
                options.elements.backgroundLayer.style.display = "block";
                options.elements.backgroundLayer.style.opacity = options.maxBackgroundLayerOpacity;
            }
        }
        else 
        {
            options.elements.backgroundLayer.style.display = "";
            options.elements.backgroundLayer.style.opacity = "";
        }
    }
    function beforeOpen(options,skipBeforeTrigger)
    {
        if( options.isBackgroundLayerEnabled ) 
        {
            options.elements.backgroundLayer.style.display = "block";
            options.elements.backgroundLayer.style.opacity = options.maxBackgroundLayerOpacity;
        }
        if( skipBeforeTrigger !== true )
        {
            mx.Core.triggerEvent(options.elements.panelContainer, "beforeOpen", false);
        }
    }
    
    function beforeClose(options)
    {
        if( options.isBackgroundLayerEnabled ) 
        {
            options.elements.backgroundLayer.style.opacity = "";
        }
        mx.Core.triggerEvent(options.elements.panelContainer, "beforeClose", false );
    }
    
    function afterOpen(options)
    {
        /*if( options.isBackgroundLayerEnabled ) 
        {
            options.elements.backgroundLayer.style.display = "block";
            options.elements.backgroundLayer.style.opacity = options.maxBackgroundLayerOpacity;
        }*/
        mx.Core.triggerEvent(options.elements.panelContainer, "afterOpen", false );
    }
    
    function afterClose(options)
    {
        if( options.isBackgroundLayerEnabled ) 
        {
            options.elements.backgroundLayer.style.display = "";
        }
        mx.Core.triggerEvent(options.elements.panelContainer, "afterClose", false );
    }
    
    function startMoving(options)
    {
        if( options.isBackgroundLayerEnabled ) 
        {
            options.elements.backgroundLayer.style.transition = "none";
        }
    }
    
    function isMoving(options,diff)
    {
        if( options.isBackgroundLayerEnabled ) 
        {
            var percent = Math.abs(diff) * 100.0 / options._.panelContainerWidth;
            options.elements.backgroundLayer.style.opacity = percent * options.maxBackgroundLayerOpacity / 100.0;
        }
    }

    function endMoving(options)
    {
        if( options.isBackgroundLayerEnabled ) 
        {
            options.elements.backgroundLayer.style.transition = "";
        }
    }

    function isOpen(options)
    {
        return options.elements.panelContainer.classList.contains(options.classes.open);
    }

    function initTopMargin(options)
    {
        options.elements.panelContainer.style.top = typeof options.topMargin === "function" ? options.topMargin() : options.topMargin;
    }

    function open(options,skipBeforeTrigger)
    {
        if( !options.elements.panelContainer.classList.contains(options.classes.open) )
        {
            initTopMargin(options);

            beforeOpen(options,skipBeforeTrigger);

            mx.Core.waitForTransitionEnd(options.elements.panelContainer, function()
            {
                // was closed again
                if( !options.elements.panelContainer.classList.contains(options.classes.open) )  return;

                if( !options.isSwipeable )
                {
                    window.addEventListener( "tapstart", options._.tapStartListener );
                    activeInstance = options.elements.panelContainer;
                }

                afterOpen(options);
            },"Panel.open",options._.transitionDuration);
            options.elements.panelContainer.classList.add(options.classes.open);

            options.elements.menuButtons.forEach(function(element){ element.classList.add(options.classes.open) });
        }
    }

    function close(options,callback)
    {
        if ( options.elements.panelContainer.classList.contains(options.classes.open) )
        {
            beforeClose(options);

            mx.Core.waitForTransitionEnd(options.elements.panelContainer, function(){
                // was open again
                if( options.elements.panelContainer.classList.contains(options.classes.open) )  return;

                if( !options.isSwipeable )
                {
                    window.removeEventListener( "tapstart", options._.tapStartListener );
                    activeInstance = null;
                }

                afterClose(options);

                if (callback) callback();
            },"Panel.close",options._.transitionDuration);
            options.elements.panelContainer.classList.remove(options.classes.open);
            options.elements.menuButtons.forEach(function(element){ element.classList.remove(options.classes.open) });
        }
        else if(callback)
        {
            callback();
        }
    }

    function isLeftPanel(options)
    {
        return options.classes.type === _options.classes.type;
    }

    function tapStart(options,e)
    {
        if( activeInstance !== null && activeInstance !== options.elements.panelContainer )
        {
            return;
        }

        var isTarget = false;
        options.elements.menuButtons.forEach(function(element){
            if( mx.Core.isEventTarget(e,element) ) isTarget = true;
        });
        if( isTarget ) return;

        var offsetX = e.detail.clientX;
        var offsetY = e.detail.clientY;

        options._.isOpen = isOpen(options);
        options._.isScrolling = null;
        
        if( !options._.panelContainerWidth )
        {
            options._.panelContainerWidth = options.elements.panelContainer.getBoundingClientRect().width;
        }

        // OPEN action is only active if the touch event is close to the left screen side
        // CLOSE action is only active if the panel is open and
        //    - the panel is fullsize (background layer is active)
        //    - or the touch event is close to the right panel side (max 20% overlapping)
        if( Math.abs(offsetX) < 45 || ( options._.isOpen && ( options.isBackgroundLayerEnabled || offsetX <= options._.panelContainerWidth * 1.2 ) ) )
        {
            initTopMargin(options);

            options._.touchStartPositionX = offsetX;
            options._.touchStartPositionY = offsetY;

            if( isLeftPanel(options) )
            {
                options._.referencePosition = options._.isOpen ? options._.panelContainerWidth : 0;
            }
            else
            {
                options._.referencePosition = options._.isOpen ? 0 : options._.panelContainerWidth;
            }

            options._.panelContainerOffset = -1;

            options._.openEventTriggered = false;

            e.stopPropagation();

            window.addEventListener( "tapmove", options._.tapMoveListener );
            window.addEventListener( "tapend", options._.tapEndListener );

            options.elements.panelContainer.classList.remove(options.classes.animation);
        }
    }

    function tapMove(options,e)
    {
        var offsetX = e.detail.clientX;
        var offsetY = e.detail.clientY;
        
        if( options._.isScrolling == null && mx.Core.isTouchDevice() ) options._.isScrolling = Math.abs(offsetX - options._.touchStartPositionX ) < Math.abs(offsetY - options._.touchStartPositionY );
        
        if( options._.isScrolling ) return;

        var diff = offsetX - options._.touchStartPositionX + options._.referencePosition;

        if( diff < 0 ) diff = 0;
        else if( diff > options._.panelContainerWidth ) diff = options._.panelContainerWidth;

        if(isLeftPanel(options))
        {
            options._.panelContainerOffset = (options._.panelContainerWidth*-1+diff);
        }
        else
        {
            options._.panelContainerOffset = diff;
        }

        if( !options._.isOpen && Math.abs(diff) > 45 && !options._.openEventTriggered )
        {
            options._.openEventTriggered = true;
            startMoving(options);
            beforeOpen(options);
        }

        options.elements.panelContainer.style.transform = "translate3d("+options._.panelContainerOffset+"px, 0, 0)";

        isMoving(options,diff);
    }

    function tapEnd(options,e)
    {
        endMoving(options);

        window.removeEventListener( "tapmove", options._.tapMoveListener );
        window.removeEventListener("tapend", options._.tapEndListener );

        if( options._.panelContainerOffset !== -1 )
        {
            if( options._.isOpen )
            {
                if( Math.abs(options._.panelContainerOffset) >= ( options._.panelContainerWidth / 3 ) ) close(options);
            }
            else if( options._.panelContainerWidth - Math.abs(options._.panelContainerOffset) >= ( options._.panelContainerWidth / 3 ) )
            {
                // beforeOpen trigger was already called during tapStart
                open(options,true);
            }
            else if(options._.openEventTriggered)
            {
                // was trying to open but it never opens
                // trigger close trigger both together
                beforeClose(options);
                afterClose(options);
            }
        }

        options.elements.panelContainer.classList.add(options.classes.animation);
        options.elements.panelContainer.style.transform = "";
    }

    ret.init = function(options)
    {
        // prepare config options
        options = mx.Core.initOptions(_options,options);

        options = mx.Core.initElements( options, "Panel","panelContainer" );
        if( options === null ) return;

        options._.openEventTriggered = false;

        function resizeHandler(){
            options._.panelContainerWidth = options.elements.panelContainer.getBoundingClientRect().width;
        }
        window.addEventListener("resize",resizeHandler);

        function clickHandler(event){
            event.stopPropagation();

            if( isOpen(options) ) close(options);
            else open(options);
        }

        options.elements.menuButtons.forEach(function(element){ element.addEventListener("click",clickHandler) });

        options._.tapStartListener = function(e){ tapStart(options,e); };
        options._.tapMoveListener = function(e){ tapMove(options,e); };
        options._.tapEndListener = function(e){ tapEnd(options,e); };

        if( options.isSwipeable )
        {
            window.addEventListener( "tapstart", options._.tapStartListener );
        }

        options.elements.panelContainer.classList.add(options.classes.type);
        options.elements.panelContainer.classList.add(options.classes.main);

        // should be delayed. Because the initial hide action should not be animated.
        window.setTimeout(function() { 
            options.elements.panelContainer.classList.add(options.classes.animation); 
            options._.transitionDuration = mx.Core.getTransitionDuration(options.elements.panelContainer);
        },10);

        return {
            isOpen: function()
            {
                return isOpen(options);
            },
            open: function()
            {
                open(options);
            },
            close: function()
            {
                close(options);
            },
            enableBackgroundLayer: function(enabled)
            {   
                enableBackgroundLayer(options,enabled);
            },
            cleanup: function(callback) {
                close(options,function()
                {
                    options.elements.panelContainer.style.top = "";
                    options.elements.panelContainer.classList.remove(options.classes.type);
                    options.elements.panelContainer.classList.remove(options.classes.main);

                    options.elements.menuButtons.forEach(function(element){ element.removeEventListener("click",clickHandler) });
                    window.removeEventListener("resize",resizeHandler);
                    window.removeEventListener( "tapstart", options._.tapStartListener );
                    window.removeEventListener( "tapmove", options._.tapMoveListener );
                    window.removeEventListener( "tapend", options._.tapEndListener );

                    if( callback !== undefined ) callback();
                });
            }
        };
    };

    return ret;
})( mx.Panel || {} );
