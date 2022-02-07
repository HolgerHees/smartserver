mx.I18N = (function( ret ) {
    var translations = {};
    
    function merge(obj1,obj2)
    {
      for( key in obj2 )
      {
          if( typeof obj1[key] === "undefined" ) obj1[key] = obj2[key];
          else Object.assign( obj1[key], obj2[key] );
      }
    }

    function push(data)
    {
        merge( translations, JSON.parse(data) );
    }

    function I18N(value) {
        this.value = value;
        
        this.fill = function(values)
        {
            if( typeof(values) == "object" && !values.hasOwnProperty("fill") )
            {
                var msg = this.value;
                for( const [key, value] of Object.entries(values) )
                {
                    msg = msg.replace("{"+key+"}",value);
                }
                return msg;
            }
            else
            {
                return this.value.replace("{}",values);
            }
        }
    }
    
    I18N.prototype.toString = function toString() {
      return this.value;
    };
    
    ret.get = function(string,component)
    {
        if( typeof component === "undefined" ) component = 'index';

        if( typeof translations[component] !== "undefined" )
        {
            if( typeof translations[component][string] !== "undefined" )
            {
                return new I18N(translations[component][string]);
            }
            else
            {
                console.error("translation key '" + string + "' for component '" + component + "' not found" );
            }
        }
               
        return new I18N(string);
    };
    
    ret.process = function(rootElement)
    {
        let elements = rootElement.querySelectorAll("*[data-i18n]");
        elements.forEach(function(element)
        {
            let key = element.getAttribute("data-i18n");               
            let values = {};
            for( let [key, value] of Object.entries(element.dataset) )
            {
                if( key.indexOf("i18n_") == -1 ) continue;
                          
                let key_data = key.split("_");
                let index = key_data[1];
                if( key_data.length > 2 )
                {
                    if( key_data[2] == "key" ) value = mx.I18N.get(value);
                }
                values[index] = value;
            }
            let i18n = mx.I18N.get(key);
            
            let values_length = Object.keys(values).length;
            if( values_length > 0 ) i18n = i18n.fill( values_length == 1 ? values[Object.keys(values)[0]].toString() : values);
            element.innerHTML = i18n;
        });
    };
    
    for (var n in mx.Translations) {
        push(mx.Translations[n]);
    }

    mx.Translations = {
        push: function(data) {
            push(data);
        }
    };

    return ret;
})( mx.I18N || {} ); 
