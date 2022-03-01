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
        
        let min_diff = 50;
        
        let old_red = parseInt(hex.slice(0, 2), 16);
        let new_red = 255 - old_red;
        let diff_red = Math.abs(old_red - new_red);
        
        if( diff_red < min_diff ) new_red = new_red > old_red ? new_red + ( min_diff - diff_red ) : new_red - ( min_diff - diff_red );

        let old_green = parseInt(hex.slice(2, 4), 16);
        let new_green = 255 - old_green;
        let diff_green = Math.abs(old_green - new_green);
        if( diff_green < min_diff ) new_green = new_green > old_green ? new_green + ( min_diff - diff_green ) : new_green - ( min_diff - diff_green );

        let old_blue = parseInt(hex.slice(4, 6), 16);
        let new_blue = 255 - old_blue;
        let diff_blue = Math.abs(old_blue - new_blue);
        if( diff_blue < min_diff ) new_blue = new_blue > old_blue ? new_blue + ( min_diff - diff_blue ) : new_blue - ( min_diff - diff_blue );
        
        // invert color components
        var r = new_red.toString(16),
            g = new_green.toString(16),
            b = new_blue.toString(16);
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
        return invertColor(mainColor);
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
    
    ret.invertColor = function(color)
    {
        return invertColor(color);
    }

    ret.init = function(imageUrl,titleUrl,finishCallback)
    {
        loadImage(imageUrl,finishCallback);
        loadTitle(titleUrl,finishCallback);
    };

    return ret;
})( mx.MainImage || {} ); 
