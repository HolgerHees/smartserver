mx.MainImage = (function( ret ) {
    var title = "";
    var copyright = "";
    var mainGray = "";
    var mainColor = "";
    var url = "";
    var finishCallback;
    
    function RGB2HSV(color) 
    {
        let parsed = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color);
        let rgb = { r: parseInt(parsed[1], 16), g: parseInt(parsed[2], 16), b: parseInt(parsed[3], 16) };

        hsv = new Object();
    	max=max3(rgb.r,rgb.g,rgb.b);
    	dif=max-min3(rgb.r,rgb.g,rgb.b);
    	hsv.saturation=(max==0.0)?0:(100*dif/max);
    	if( hsv.saturation==0 ) hsv.hue=0;
     	else if( rgb.r==max ) hsv.hue=60.0*(rgb.g-rgb.b)/dif;
    	else if( rgb.g==max ) hsv.hue=120.0+60.0*(rgb.b-rgb.r)/dif;
    	else if( rgb.b==max ) hsv.hue=240.0+60.0*(rgb.r-rgb.g)/dif;
    	if( hsv.hue<0.0 ) hsv.hue+=360.0;
    	hsv.value=Math.round(max*100/255);
    	hsv.hue=Math.round(hsv.hue);
    	hsv.saturation=Math.round(hsv.saturation);
    	return hsv;
    }
    
    function HSV2RGB(hsv) 
    {
    	var rgb=new Object();
    	if( hsv.saturation==0 ) 
        {
    		rgb.r=rgb.g=rgb.b=Math.round(hsv.value*2.55);
    	}
    	else 
        {
    		hsv.hue/=60;
    		hsv.saturation/=100;
    		hsv.value/=100;
    		i=Math.floor(hsv.hue);
    		f=hsv.hue-i;
    		p=hsv.value*(1-hsv.saturation);
    		q=hsv.value*(1-hsv.saturation*f);
    		t=hsv.value*(1-hsv.saturation*(1-f));
    		switch(i) {
                case 0: rgb.r=hsv.value; rgb.g=t; rgb.b=p; break;
                case 1: rgb.r=q; rgb.g=hsv.value; rgb.b=p; break;
                case 2: rgb.r=p; rgb.g=hsv.value; rgb.b=t; break;
                case 3: rgb.r=p; rgb.g=q; rgb.b=hsv.value; break;
                case 4: rgb.r=t; rgb.g=p; rgb.b=hsv.value; break;
                default: rgb.r=hsv.value; rgb.g=p; rgb.b=q;
    		}
    		rgb.r=Math.round(rgb.r*255);
    		rgb.g=Math.round(rgb.g*255);
    		rgb.b=Math.round(rgb.b*255);
    	}
    	
    	return "#" + rgb.r.toString(16) + rgb.g.toString(16) + rgb.b.toString(16);
    }

    function HueShift(h,s) 
    { 
        h+=s; while (h>=360.0) h-=360.0; while (h<0.0) h+=360.0; return h; 
    }
    function min3(a,b,c) 
    { 
        return (a<b)?((a<c)?a:c):((b<c)?b:c); 
    } 
    function max3(a,b,c) 
    { 
        return (a>b)?((a>c)?a:c):((b>c)?b:c); 
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

    ret.getComplementaryColor = function()
    {
        let hsv=RGB2HSV(mainColor);
        hsv.hue=HueShift(hsv.hue,180.0);
        return HSV2RGB(hsv);
    };

    ret.getComplementaryGray = function()
    {
        let hsv=RGB2HSV(mainGray);
        hsv.hue=HueShift(hsv.hue,180.0);
        return HSV2RGB(hsv);
    };

    ret.init = function(imageUrl,titleUrl,finishCallback)
    {
        loadImage(imageUrl,finishCallback);
        loadTitle(titleUrl,finishCallback);
    };

    return ret;
})( mx.MainImage || {} ); 
