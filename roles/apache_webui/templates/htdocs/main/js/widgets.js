mx.Widgets = (function( ret ) {
    widgets = [];

    /*let last_needed_size = -1;
    let last_max_size = -1;
    let left_mode = true;*/

    let max_size = 0;
    let widgets_sizes = {};
    let possible_left_widgets = [];
    let spacer_widget = null;

    let last_needed_size = 0;
    let last_max_size = 0;

    ret.get = function()
    {
        result = [];
        widgets.forEach(function(widget, index)
        {
            for( let i = 0; i < widget.getCount(); i++ )
            {
                widget.reset();
                let onclick = widget.hasAction(i) ? " onclick=\"mx.Widgets.click(this, '" + index + "', '" + i + "')\"" : "";
                let css = widget.hasAction(i) ? " clickable" : ""
                let position = widget.getOrder(i) <= 500 ? "left": "right";
                css += " " + ( position == "left" ? "possibleLeft left" : "right" );
                result.push([ widget.getOrder(i), position, "<div" + onclick + " class=\"widget" + css + "\" id=\"" + widget.getId(i) + "\"></div>" ]);
            }
        });

        result.sort(function(a,b)
        {
            if( a[0] < b[0] ) return -1;
            if( a[0] > b[0] ) return 1;
            return 0;
        });

        _result = [];
        _last_position = "left"
        result.forEach(function(data)
        {
            if( _last_position != data[1] )
            {
                _result.push("<div class=\"spacer\"></div>");
                _last_position = data[1];
            }
            _result.push(data[2]);
        });

        if( _last_position == "left" ) _result.push("<div class=\"spacer\"></div>");

        return _result;
    }

    ret.init = function(innerRoot, outerRoot) {
        spacer_widget = mx._$(".spacer", innerRoot);
        possible_left_widgets = mx._$$(".possibleLeft", innerRoot);
        let widgets = mx._$$(".widget", innerRoot)
        widgets.forEach(function(widget)
        {
            new ResizeObserver(mx.Widgets.handleResize).observe(widget);
        });
        new ResizeObserver(mx.Widgets.handleResize).observe(outerRoot);
    }

    ret.handleResize = function(events) {
        //let max_size = mx.$(".service.home .widgets").scrollWidth;

        for( i in events )
        {
            let event = events[i];
            //console.log(event);
            let id = event["target"].id;
            if( id )
            {
                widgets_sizes[id] = event["contentRect"]["width"] + 5;
            }
            else
            {
                max_size = Math.round(event["contentRect"]["width"]);
            }
        }

        needed_size = 0;
        for( id in widgets_sizes )
        {
            needed_size += widgets_sizes[id];
        }
        needed_size = Math.round(needed_size);

        if( last_needed_size != needed_size || last_max_size != max_size )
        {
            //console.log(max_size + " " + needed_size);
            if( needed_size > max_size )
            {
                spacer_widget.style.display = "none";
                possible_left_widgets.forEach(function(widget)
                {
                    widget.classList.remove("left")
                    widget.classList.add("right")
                });
            }
            else
            {
                spacer_widget.style.display = "";
                possible_left_widgets.forEach(function(widget)
                {
                    widget.classList.remove("right")
                    widget.classList.add("left")
                });
            }
            last_needed_size = needed_size;
            last_max_size = max_size;
        }
    }

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

                callback(null);
                //mx.Page.handleRequestError(this.status, url,function(){ mx.Widgets.fetchContent(method, url, callback, data ) }, timeout);
            }
        };

        if( data) xhr.send( data );
        else xhr.send();
    }
    ret.register = function(widget, index)
    {
        widgets.push(widget);
    }

    ret.preload = function( callback )
    {
        if( widgets.length == 0 )
        {
            callback();
        }
        else
        {
            widgets.forEach(function(widget, index)
            {
                widget._preload = [];
                for( let i = 0; i < widget.getCount(); i++ )
                {
                    widget._preload[i] = null;
                }
            });
            widgets.forEach(function(widget)
            {
                widget._show = widget.show;
                widget.show = function(index, msg)
                {
                    widget._preload[index] = msg;

                    let missing_preloads = widgets.filter( (widget) => widget._preload.filter( (preload) => preload == null ).length > 0  );
                    if( missing_preloads.length == 0 ) callback();
                };
                widget.refresh();
            });
        }
    }

    ret.refresh = function()
    {
        widgets.forEach(function(widget)
        {
            if( widget._preload != undefined )
            {
                widget.show = widget._show;
                widget._preload.forEach( (msg,index) => widget.show(index, msg) );
                delete widget._show;
                delete widget._preload;
            }
            else
            {
                widget.refresh();
            }
        });
    }

    ret.click = function( event, index, i )
    {
        widgets[index].click(event, i);
    }

    return ret;
})( mx.Widgets || {} );

mx.Widgets.Object = function(group, config)
{
    return (function( ret ) {
        let last_msg = {};
        ret.getId = function(index) { return config[index]["id"]; }
        ret.getOrder = function(index) { return config[index]["order"]; }
        ret.getCount = function() { return config.length; }
        ret.getElement = function(index) { return mx.$("#"+ config[index]["id"] ) ; }
        ret.hasAction = function(index) { return config[index]["click"] != undefined; }
        ret.click = function(event, index) { config[index]["click"](event); }
        ret.reset = function(){ last_msg = {}; }
        ret.alert = function(index, msg)
        {
            ret.show(index, "<span class=\"error\">" + msg + "</span>");
        }
        ret.show = function(index, msg)
        {
            let isInitialLoad = last_msg[index] == undefined

            if( isInitialLoad || last_msg[index] != msg )
            {
                let div = mx.$("#" + config[index]["id"]);
                let old_width = div.scrollWidth;

                // calculate new width to calculate scrollWidth
                div.style.transition = "none";
                div.style.width = "";
                div.innerHTML = msg;
                let new_width = div.scrollWidth;

                // restore layout (width & transtion)
                div.style.width = old_width + "px";
                div.scrollWidth; // force releayout
                if( !isInitialLoad )
                {
                    div.style.transition = "";
                }

                if( msg )
                {
                    div.style.width = new_width + "px";
                    div.style.marginRight = "";
                }
                else
                {
                    div.style.width = "0";
                    div.style.marginRight = "-5px";
                }

                if( isInitialLoad )
                {
                    div.scrollWidth; // force releayout
                    div.style.transition = "";
                }

                last_msg[index] = msg;
            }
        }
        if( mx.User.memberOf(group) ) mx.Widgets.register(ret);
        return ret;
    })( {} );
}
