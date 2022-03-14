mx.UpdateServiceHelper = (function( ret ) {
    let hasError = false;
    let isRestarting = false;
    
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
    
    function hideError()
    {
        if( !hasError ) return;
        hasError = false;

        let elements = document.body.childNodes;
        for( let i = 0; i < elements.length; i++ )
        {
            let element = elements[i];
            if( element.nodeType == Node.TEXT_NODE ) continue;
            if( element.classList.contains("error") )
            {
                element.style.display = "none";
            }
            else
            {
                if( element.hasAttribute("data-olddisplay") )
                {
                    element.style.display = element.getAttribute("data-olddisplay");
                    element.removeAttribute("data-olddisplay");
                }
            }
        }
    }

    function showError(message)
    {
        if( hasError ) return;
        hasError = true;
        
        let elements = document.body.childNodes;
        for( let i = 0; i < elements.length; i++ )
        {
            let element = elements[i];
            if( element.nodeType == Node.TEXT_NODE ) continue;
            if( element.classList.contains("error") )
            {
                element.style.display = "";
                element.innerHTML = "<div>" + message + "</div>";
            }
            else if( element.style.display != "none" )
            {
                element.setAttribute("data-olddisplay", "" + element.style.display);
                element.style.display = "none";
            }
        }
    }
    
    ret.handleServerError = function( response )
    {
        alert(response["message"]);
    }
    
    ret.handleRequestError = function( code, text, response )
    {
        //console.log(response);
        alert(mx.I18N.get("Service Error") + " '" + code + " " + text + "'" );
    }
    
    ret.handleServerNotAvailable = function()
    {
        showError( mx.I18N.get( isRestarting ? "Service is restarting" : "Service is currently not available") );
    }
    
    ret.confirmSuccess = function()
    {
        hideError();
        isRestarting = false;
    }

    ret.announceRestart = function()
    {
        isRestarting = true
        window.setTimeout(function(){ isRestarting = false; },5000);
    }
    
    ret.isRestarting = function()
    {
        return isRestarting;
    }

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

    ret.setElementContent = function(content, id)
    {
        var element = mx.$("#" + id);
        if( element.dataset.content != content )
        {
            element.dataset.content = content;
            element.innerHTML = content;
            element.style.display = content ? "" : "None";
        }
    }
    
    ret.setTableContent = function(tableContent, tableId, headerContent, headerId)
    {
        var headerElement = mx.$("#" + headerId);
        var tableElement = mx.$("#" + tableId);
        if( !headerContent )
        {
            if( headerElement.style.display != "none" )
            {
                headerElement.dataset.content = "";
                headerElement.innerHTML = "";
                headerElement.style.display = "none";
            }
            if( tableElement.style.display != "none" )
            {
                tableElement.dataset.content = "";
                tableElement.innerHTML = "";
                tableElement.style.display = "none";
            }
        }
        else
        {
            if( headerElement.dataset.content != headerContent )
            {
                headerElement.dataset.content = headerContent;
                headerElement.innerHTML = headerContent;
                headerElement.style.display = "";
            }
            if( tableElement.dataset.content != tableContent )
            {
                tableElement.dataset.content = tableContent;
                tableElement.innerHTML = tableContent
                tableElement.style.display = "";
            }
            
            mx.UpdateServiceHelper.setToogle(mx.$("#" + headerId + " .form.button.toggle"),tableElement);
            fixScrollHeight(tableElement);
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
