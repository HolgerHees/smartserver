mx.Widgets = (function( ret ) {
    widgets = [];

    ret.fetchContent = function(method, url, callback, data)
    {
        var xhr = new XMLHttpRequest();
        xhr.open(method, url );
        if( method == "POST" ) xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;

            if( this.status == 200 )
            {
                if( callback ) callback(this.response);
            }
            else
            {
                let timeout = 15000;

                mx.Page.handleRequestError(url,function(){ mx.Widgets.fetchContent(url, callback) }, timeout);
            }
        };

        if( data) xhr.send( data );
        else xhr.send();
    }
    ret.register = function(widget, index)
    {
        widgets.push(widget);
    }

    ret.refresh = function()
    {
        widgets.forEach(function(widget)
        {
            widget.refresh();
        });
    }

    ret.click = function( event, index, i )
    {
        widgets[index].click(event, i);
    }

    ret.get = function()
    {

        /*let _widgets = {};

        for( key in keys )
        {
            _widgets[keys[key].toString()] = widgets[keys[key]];
        }*/

        result = [];
        widgets.forEach(function(widget, index)
        {
            for( let i = 0; i < widget.getCount(); i++ )
            {
                let onclick = widget.hasAction(i) ? " onclick=\"mx.Widgets.click(this, '" + index + "', '" + i + "')\"" : "";
                let css = widget.hasAction(i) ? " clickable" : ""
                result.push([ widget.getOrder(i), "<div" + onclick + " class=\"widget" + css + "\" id=\"" + widget.getId(i) + "\"></div>" ]);
            }
        });

        result.sort(function(a,b)
        {
            if( a[0] < b[0] ) return -1;
            if( a[0] > b[0] ) return 1;
            return 0;
        });

        _result = [];
        result.forEach(function(data)
        {
            _result.push(data[1]);
        });

        return _result;
    }

    return ret;
})( mx.Widgets || {} );

mx.Widgets.Object = function(group, config)
{
    return (function( ret ) {
        ret.getId = function(index) { return config[index]["id"]; }
        ret.getOrder = function(index) { return config[index]["order"]; }
        ret.getCount = function() { return config.length; }
        ret.getElement = function(index) { return mx.$("#"+ config[index]["id"] ) ; }
        ret.hasAction = function(index) { return config[index]["click"] != undefined; }
        ret.click = function(event, index) { config[index]["click"](event); }
        ret.show = function(index)
        {
            let div = mx.$("#" + config[index]["id"]);
            div.style.width = div.scrollWidth + "px";
            div.style.marginRight = "";
        }
        ret.hide = function(index)
        {
            let div = mx.$("#" + config[index]["id"]);
            div.style.width = 0;
            div.style.marginRight = "-5px";

        }
        if( mx.User.memberOf(group) ) mx.Widgets.register(ret);
        return ret;
    })( {} );
}
