mx.MainImage = (function( ret ) {
    var title = "";
    var url = "";
    var finishCallback;
    
    function loadImage(imageUrl,finishCallback)
    {
        var id = Math.round( Date.now() / 1000 / ( 60 * 60 ) );
        var src = imageUrl + '?' + id;
        var img = new Image();
        img.onload = function()
        {
            url = src;
            finishCallback();
        };
        img.onerror = function()
        {
            finishCallback();
        };
        img.src = src;
    }

    function loadTitle(titleUrl,finishCallback)
    {
        var id = Math.round( Date.now() / 1000 / ( 60 * 60 ) );
        //mx.Actions.openMenu(mx.$('#defaultEntry'),"nextcloud");
        var xhr = new XMLHttpRequest();
        xhr.open("GET", titleUrl + '?' + id);
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) title = this.response;
            else alert("was not able to download '" + titleUrl + "'");
            finishCallback();
        };
        xhr.send();
    }

    ret.getUrl = function()
    {
        return url;
    }

    ret.getTitle = function()
    {
        return title;
    }

    ret.init = function(imageUrl,titleUrl,finishCallback)
    {
        loadImage(imageUrl,finishCallback);
        loadTitle(titleUrl,finishCallback);
    }

    return ret;
})( mx.MainImage || {} ); 
