mx.Table = (function( ret ) {
    var _options = {
        "class": null,
        "sort": null, //{ "value": null, "reverse": null, "callback": null },
        "header": [], // { "class": null, "grow": false, "sort": null, "value": null }
        "rows": [] // { "class": null, "onclick": null, "columns": [ { "class": null, "value": null, "data": {} } ] }
    };
    
    function build(options,tableElement)
    {
        tableElement.className = "form table" + ( options["class"] ? " " + options["class"] : "" );
        
        let content = "<div class=\"row";
        content += "\">";
        options["header"].forEach(function(column)
        {
            let cls = [];
            if( column["grow"] ) cls.push("grow");
            if( column["class"] ) cls.push(column["class"]);
            if( column["align"] ) cls.push(column["align"] == "left" ? "left-align" : "right-align");
            if( options["sort"] ) cls.push("sort");
            
            content += "<div";
            if( options["sort"] ) content += " onclick=\"" + options["sort"]["callback"] + "('" + column["sort"]["value"] + "'," + ( options["sort"]["reverse"] ? 'false' : 'true' ) + ")\"";

            if( cls.length ) content += " class=\"" + cls.join(" ") + "\"";
            content += ">";
            if( column["value"] ) content += column["value"];
            
            if( options["sort"] && column["sort"]["value"] == options["sort"]["value"] ) content += "<span class=\"" + ( options["sort"]["reverse"] ? "icon-up": "icon-down-1" ) + "\"></span> ";
            
            content += "</div>";
        });
        content += "</div>";

        options["rows"].forEach(function(row)
        {
            content += "<div class=\"row";
            let cls = [];
            if( row["class"] ) cls.push(row["class"]);
            if( cls.length ) content += " " + cls.join(" ");
            content += "\"";
            if( row["onclick"] ) content += "onclick=\"" + row["onclick"] + "\"";
            content += ">";

            row["columns"].forEach(function(column,i)
            {
                let cls = [];
                if( options["header"][i]["grow"] ) cls.push("grow");
                if( column["class"] ) cls.push(column["class"]);
                if( column["align"] ) cls.push(column["align"] == "left" ? "left-align" : "right-align");

                content += "<div";
                if( cls.length ) content += " class=\"" + cls.join(" ") + "\"";
                if( column["data"] )
                {
                    Object.keys(column["data"]).forEach(function(key)
                    {
                        content += " data-" + key + "=\"" + column["data"][key] + "\"";
                    });
                }
                content += ">";
                if( column["value"] ) content += column["value"];
                content += "</div>";
            });
            content += "</div>";
        });
        
        tableElement.innerHTML = content;
    }

    ret.init = function(options)
    {
        // prepare config options
        options = mx.Core.initOptions(_options,options);

        options = mx.Core.initElements( options, "Table" );
        if( options === null ) return;

 
        return {
            'build': function(tableElement)
            {
                return build(options,tableElement)
            }
        };
    };

    return ret;
})( mx.Table || {} );
