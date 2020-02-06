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

    ret.get = function(string,component)
    {
        if( typeof component === "undefined" ) component = 'index';

        if( typeof translations[component] !== "undefined" )
        {
            if( typeof translations[component][string] !== "undefined" )
            {
                return translations[component][string];
            }
            else
            {
                console.error("translation key '" + string + "' for component '" + component + "' not found" );
            }
        }
        return string;
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
