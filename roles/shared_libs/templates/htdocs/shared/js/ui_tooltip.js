mx.Tooltip = (function( ret ) {
    let tooltip = null;
    let tooltipArrow = null;
    let tooltipText = null;
    
    function create()
    {
        tooltip = document.createElement("div");
        tooltip.className = "tooltip";
        tooltip.innerHTML = "<span class=\"text\"></span><span class=\"arrow\"></span>";
        tooltipText = tooltip.querySelector(".text");
        tooltipArrow = tooltip.querySelector(".arrow");
        document.body.appendChild(tooltip);
    }

    ret.getRootElementRect = function()
    {
        if( tooltip == null ) create();

        return tooltip.getBoundingClientRect();
    }

    ret.getRootElement = function()
    {
        return tooltip;
    }

    ret.getArrowElementRect = function()
    {
        if( tooltip == null ) create();

        return tooltipArrow.getBoundingClientRect();
    }

    ret.hide = function()
    {
        if( tooltip == null ) create();

        tooltip.classList.remove("active");
    }
    
    ret.setText = function(text)
    {
        if( tooltip == null ) create();

        tooltipText.innerHTML = text;
    }
    
    ret.show = function( tooltipLeft, tooltipTop, arrowOffset, arrowPosition)
    {
        if( tooltip == null ) create();
        
        tooltip.style.cssText = "left: " + tooltipLeft + "px; top: " + tooltipTop + "px;";
        
        if( !arrowPosition ) arrowPosition = "bottom";
        
        tooltipArrow.className = "arrow " + arrowPosition;

        if( arrowPosition == "top" || arrowPosition == "bottom" )
        {
            tooltipArrow.style.left = arrowOffset;
        }
        else
        {
            tooltipArrow.style.top = arrowOffset;
        }
        tooltip.classList.add("active");
    }
    
    ret.toggle = function()
    {
        tooltip.classList.toggle("active");
    }

    ret.init = function()
    {
        let tooltipDataSets = mx.$$("[data-tooltip]");
        tooltipDataSets.forEach(function(element)
        {
            element.addEventListener("mouseenter", function( event ) {
                
                mx.Tooltip.setText(element.dataset.tooltip);
                
                let elementParentRect = element.parentNode.getBoundingClientRect();
                let elementRect = element.getBoundingClientRect();
                
                let tooltipRect = mx.Tooltip.getRootElementRect();
                
                let leftPos = ( elementRect.left + elementRect.width / 2 - tooltipRect.width / 2 )
                let topPos = elementRect.top - tooltipRect.height;
                
                let arrowLeft = "calc(50% - " + (mx.Tooltip.getArrowElementRect().width / 2 - 1) + "px)";
                
                mx.Tooltip.show(leftPos, topPos, arrowLeft);

                window.setTimeout(function(){ tooltip.style.opacity="1"; },0);
            });
            element.addEventListener("mouseout", function( event ) {
                tooltip.style.opacity="0";
                mx.Tooltip.hide();
            });
        });
    }
    
    return ret;
})( mx.Tooltip || {} );
