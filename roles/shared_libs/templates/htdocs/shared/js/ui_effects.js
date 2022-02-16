mx.Effects = (function( ret ) {
    function createRipple(event) {
        const button = event.currentTarget;
        
        const circle = document.createElement("span");
        const diameter = Math.max(button.clientWidth, button.clientHeight);
        const radius = diameter / 2;
        
        var offsets = mx.Core.getOffsets(button);
        
        circle.style.width = circle.style.height = diameter + "px";
        circle.style.left = ( event.clientX - (offsets.left + radius) ) + "px";
        circle.style.top = ( event.clientY - (offsets.top + radius) ) + "px";
        circle.classList.add("ripple"); 
        
        const ripple = button.getElementsByClassName("ripple")[0];

        if (ripple) ripple.remove();
           
        button.appendChild(circle);
    }
    
    ret.init = function(rootElement)
    {
        const buttons = mx.$$(".form.button");
        for (const button of buttons) 
        {
            if( button.dataset.ripple ) continue;

            button.dataset.ripple = 1
            button.addEventListener("click", createRipple);
        }
    };

    return ret;
})( mx.Effects || {} );
