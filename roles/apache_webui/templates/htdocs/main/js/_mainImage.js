mx.MainImage = (function( ret ) {
    var title = "";
    var copyright = "";
    var mainGray = "";
    var mainColor = "";
    var url = "";
    var finishCallback;
    
    function invertColor(hex) {
        if (hex.indexOf('#') === 0) {
            hex = hex.slice(1);
        }
        // convert 3-digit hex to 6-digits.
        if (hex.length === 3) {
            hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
        }
        if (hex.length !== 6) {
            throw new Error('Invalid HEX color.');
        }
        // invert color components
        var r = (255 - parseInt(hex.slice(0, 2), 16)).toString(16),
            g = (255 - parseInt(hex.slice(2, 4), 16)).toString(16),
            b = (255 - parseInt(hex.slice(4, 6), 16)).toString(16);
        // pad each with zeros and return
        return '#' + mx.MainImage.padZero(r) + mx.MainImage.padZero(g) + mx.MainImage.padZero(b);
    }

    function loadImage(imageUrl,finishCallback)
    {
        var id = Math.round( Date.now() / 1000 / ( 60 * 60 ) );
        var src = imageUrl + '?' + id;
        
        var xhr = new XMLHttpRequest();
        xhr.open("GET", src);
        xhr.withCredentials = true;
        xhr.responseType = 'blob';
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                url = window.URL.createObjectURL(this.response);
                finishCallback();
            }
            else
            {
                finishCallback();
            }
        };
        xhr.send();
    }

    function loadTitle(titleUrl,finishCallback)
    {
        var id = Math.round( Date.now() / 1000 / ( 60 * 60 ) );
        //mx.Actions.openMenu(mx.$('#defaultEntry'),"nextcloud");
        var xhr = new XMLHttpRequest();
        xhr.open("GET", titleUrl + '?' + id);
        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                let data = this.response.split("\n");
                title = data[0];
                copyright = data[1];
                mainColor = data[2];
                mainGray = data[3];
            }
            else alert("was not able to download '" + titleUrl + "'");
            finishCallback();
        };
        xhr.send();
    }

    ret.getUrl = function()
    {
        return url;
    };

    ret.getTitle = function()
    {
        return title;
    };

    ret.getCopyright = function()
    {
        return copyright;
    };
    
    ret.padZero = function(str, len) {
        len = len || 2;
        var zeros = new Array(len).join('0');
        return (zeros + str).slice(-len);
    }

    ret.getLuminance = function(color)
    {
        let parsed = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color ? color : mainColor);
        let rgb = { r: parseInt(parsed[1], 16), g: parseInt(parsed[2], 16), b: parseInt(parsed[3], 16) };
        let luminance = (0.2126*rgb.r + 0.7152*rgb.g + 0.0722*rgb.b);
        return luminance;
    }

    ret.getColor = function()
    {
        return mainColor;
    }
    
    ret.getComplementaryColor = function()
    {
        let parsed = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(mainColor);
        let rgb = { r: parseInt(parsed[1], 16), g: parseInt(parsed[2], 16), b: parseInt(parsed[3], 16) };
        rgb.r = 256 - rgb.r;
        rgb.g = 256 - rgb.g;
        rgb.b = 256 - rgb.b;
        
        // pad each with zeros and return
        return '#' + padZero(rgb.r.toString(16)) + padZero(rgb.g.toString(16)) + padZero(rgb.b.toString(16));
        
        //return invertColor(mainColor);
        //let hsv=RGB2HSV(mainColor);
        //hsv.hue=HueShift(hsv.hue,180.0);
        //return invertColor(mainColor);
    };

    ret.getGray = function()
    {
        return mainGray;
    }

    ret.getComplementaryGray = function()
    {
        return invertColor(mainGray);
        //let hsv=RGB2HSV(mainGray);
        //hsv.hue=HueShift(hsv.hue,180.0);
        //return HSV2RGB(hsv);
    };

    ret.init = function(imageUrl,titleUrl,finishCallback)
    {
        loadImage(imageUrl,finishCallback);
        loadTitle(titleUrl,finishCallback);
    };

    return ret;
})( mx.MainImage || {} ); 
