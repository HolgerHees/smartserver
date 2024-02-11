mx.UpdateServiceHelper = (function( ret ) {
    ret.setToogle = function(btnElement,detailElement)
    {
        if( btnElement != null ) 
        {
            let icon = detailElement.style.maxHeight ? "icon-play open" : "icon-play";
            if( btnElement.childNodes.length > 0 ) btnElement.childNodes[0].className = icon;
            else btnElement.innerHTML = "<span class=\"" + icon + "\"></span>";
        }
    }

    ret.setScrollHeight = function(element)
    {
        var limitHeight =  Math.round(window.innerHeight * 0.8);
        var maxHeight = ( element.scrollHeight + 20 );
        if( maxHeight > limitHeight )
        {
            maxHeight = limitHeight;
            element.style.overflowY = "scroll";
        }
        else
        {
            element.style.overflowY = "";
        }
        element.style.maxHeight = maxHeight + "px"; 
    }
    
    ret.setExclusiveButtonsState = function(flag, excludeClass)
    {
        if( flag )
        {
            mx.$$("div.form.button.exclusive:not(.blocked)").forEach(function(element)
            { 
                if( excludeClass != null && element.classList.contains(excludeClass) )
                {
                    element.classList.add("disabled"); 
                }
                else
                {
                    element.classList.remove("disabled");
                }
            });
        }
        else
        {
            mx.$$("div.form.button.exclusive:not(.blocked)").forEach(function(element)
            {
                if( excludeClass != null && element.classList.contains(excludeClass) )
                {
                    element.classList.remove("disabled");
                }
                else
                {
                    element.classList.add("disabled");
                }
            });
        }
    }

    ret.initTable = function(headerElement,tableElement)
    {
        mx.UpdateServiceHelper.setToogle(headerElement.querySelector(".form.button.toggle"),tableElement);
        if( tableElement.style.maxHeight )
        {
            if( tableElement.innerHTML )
            {
                tableElement.style.display = "block";
                mx.UpdateServiceHelper.setScrollHeight(tableElement)
            }
            else
            {
                tableElement.style.maxHeight = "";
                tableElement.style.display = "";
            }
        }
    }
    
    ret.toggleTable = function(btn,id)
    {
        var element = mx.$("#"+id);
        if( element.style.maxHeight )
        {
            element.style.maxHeight = "";
            mx.UpdateServiceHelper.setToogle(btn,element);
            window.setTimeout(function(){ element.style.display=""; },300);
        }
        else
        {
            element.style.display = "block";
            window.setTimeout(function(){ 
                mx.UpdateServiceHelper.setScrollHeight(element);
                mx.UpdateServiceHelper.setToogle(btn,element); 
            },0);
        }
    }
    
    ret.setLastCheckedContent = function(dateFormatted,id)
    {
        var element = mx.$("#" + id);
        if( dateFormatted ) element.innerHTML = "(" + dateFormatted + ")";
        else element.innerHTML = "";
    }
    
    function cleanTime(time)
    {
        return time.substring(0,time.length - 3);
    }
    
    ret.formatDate = function(date)
    {
        if( date )
        {
            if( date.toLocaleDateString() == (new Date()).toLocaleDateString() )
            {
                return [ mx.I18N.get("Today, {}").fill(cleanTime(date.toLocaleTimeString())), "today" ];
            }
            else if( date.toLocaleDateString() == ( new Date(new Date().getTime() - 24*60*60*1000) ).toLocaleDateString() )
            {
                return [ mx.I18N.get("Yesterday, {}").fill(cleanTime(date.toLocaleTimeString())), "yesterday" ];
            }
            else
            {
                return [ cleanTime(date.toLocaleString()), "other" ];
            }
        }
        else
        {
            return [ null, null ];
        }
    }
    
    return ret;
})( mx.UpdateServiceHelper || {} ); 
