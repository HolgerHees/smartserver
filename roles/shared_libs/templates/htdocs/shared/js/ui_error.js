mx.Error = (function( ret ) {
    let hasError = false;
    let errorLayer = null;
    
    function hideError()
    {
        if( !hasError ) return;
        hasError = false;

        let elements = document.body.childNodes;
        for( let i = 0; i < elements.length; i++ )
        {
            let element = elements[i];
            if( element.nodeType == Node.TEXT_NODE ) continue;
            if( element.isSameNode(errorLayer) )
            {
                element.style.display = "";
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

        if( !errorLayer )
        {
            errorLayer = mx.$("div.contentLayer.error");
            if( !errorLayer )
            {
                errorLayer = document.createElement("div");
                errorLayer.classList.add("contentLayer");
                errorLayer.classList.add("error");
                document.body.appendChild(errorLayer);
            }
        }
        
        let elements = document.body.childNodes;
        for( let i = 0; i < elements.length; i++ )
        {
            let element = elements[i];
            if( element.nodeType == Node.TEXT_NODE ) continue;
            if( element.isSameNode(errorLayer) )
            {
                element.style.display = "block";
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
    
    ret.handleError = function( message )
    {
        showError( message );
    }
    
    ret.confirmSuccess = function()
    {
        hideError();
    }
    
    return ret;
    
})( mx.Error || {} );
