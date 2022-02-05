mx.UpdateServiceHelper = (function( ret ) {
    function fixScrollHeight(element)
    {
        if( element.style.maxHeight )
        {
            if( element.innerHTML )
            {
                element.style.display = "block";
                mx.UpdateServiceHelper.setScrollHeight(element)
            }
            else
            {
                element.style.maxHeight = "";
                element.style.display = "";
            }
        }
    }

    ret.handleServerError = function( response )
    {
        alert(response["message"]);
    }
    
    ret.handleRequestError = function( code, text )
    {
        alert("error '" + code + " " + text + "'");
    }
    
    ret.setToogle = function(btnElement,detailElement)
    {
        if( btnElement != null ) btnElement.innerText = detailElement.style.maxHeight ? mx.I18N.get("Hide") : mx.I18N.get("Show");
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

    ret.setTableContent = function(tableContent, tableId, headerContent, headerId)
    {
        var headerElement = mx.$("#" + headerId);
        var tableElement = mx.$("#" + tableId);
        if( !headerContent )
        {
            headerElement.style.display = "none";
            tableElement.style.display = "none";
        }
        else
        {
            headerElement.innerHTML = headerContent;
            headerElement.style.display = "";
            tableElement.innerHTML = tableContent
            tableElement.style.display = "";
            
            mx.UpdateServiceHelper.setToogle(mx.$("#" + headerId + " .form.button.toggle"),tableElement);
            fixScrollHeight(tableElement);
        }
    }

    ret.setLastCheckedContent = function(dateFormatted,id)
    {
        var element = mx.$("#" + id);
        if( dateFormatted ) element.innerHTML = "(" + mx.I18N.get("checked on") + " " + dateFormatted + ")";
        else element.innerHTML = "(" + mx.I18N.get("never checked") + ")";
    }
        
    return ret;
})( mx.UpdateServiceHelper || {} ); 
