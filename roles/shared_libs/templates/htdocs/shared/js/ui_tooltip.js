mx.Tooltip = (function( ret ) {
    let tooltip = null;
    let tooltipArrow = null;
    let tooltipText = null;

    function positionSlotTooltip(element)
    {        
        var elementParentRect = element.parentNode.getBoundingClientRect();
        var elementRect = element.getBoundingClientRect();
        var tooltipRect = tooltip.getBoundingClientRect();
        var tooltipArrowRect = tooltipArrow.getBoundingClientRect();
        
        var leftPos = ( elementRect.left + elementRect.width / 2 - tooltipRect.width / 2 )
        let topPos = elementRect.top - tooltipRect.height;
        
        tooltipArrow.style.left = "calc(50% - " + (tooltipArrowRect.width / 2 - 1) + "px)";
            
        tooltip.style.cssText = "left: " + leftPos + "px; top: " + topPos + "px;";
    }
    
    function show(element)
    {
        tooltip.classList.add("active");
        window.setTimeout(function(){ tooltip.style.opacity="1"; },0);
        tooltipText.innerHTML = element.dataset.tooltip;

        positionSlotTooltip(element);
    }
    
    function hide()
    {
        tooltip.style.opacity="0";
        tooltip.classList.remove("active");
    }
    
    ret.create = function()
    {
        if( tooltip ) return;
        
        tooltip = document.createElement("div");
        tooltip.className = "tooltip";
        tooltip.innerHTML = "<span class=\"text\"></span><span class=\"arrow\"></span>";
        tooltipText = tooltip.querySelector(".text");
        tooltipArrow = tooltip.querySelector(".arrow");
        document.body.appendChild(tooltip);
    }
    
    ret.init = function()
    {
        mx.Tooltip.create();
        
        let tooltipDataSets = mx.$$("[data-tooltip]");
        tooltipDataSets.forEach(function(element)
        {
            element.addEventListener("mouseenter", function( event ) {
                show(element);
            });
            element.addEventListener("mouseout", function( event ) {
                hide();
            });
        });
    }
    
    return ret;
})( mx.Tooltip || {} );
