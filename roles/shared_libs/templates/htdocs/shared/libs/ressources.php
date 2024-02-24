<?php
class Ressources
{
    private static function getLang()
    {
        $lang = isset($_SERVER['HTTP_ACCEPT_LANGUAGE']) ? $_SERVER['HTTP_ACCEPT_LANGUAGE'] : "";
        $lang = strpos($lang,"de") !== false ? 'de' : '';
        return $lang;
    }

    private static function getI18NFile($dir)
    {
        $lang = Ressources::getLang();
        $i18n_file = $dir . '../i18n/' . $lang . '.json';
        return is_file( $i18n_file ) ? $i18n_file : null;
    }

    private static function getI18NContent($i18n_file)
    {
        $stream = fopen($i18n_file, 'r');
        $content = stream_get_contents($stream);
        $content = str_replace("'","\\'",$content);
        $content = str_replace("\n","",$content);
        $content = "mx.Translations.push('".$content."');\n";
        fclose($stream);
        return $content;
    }

    private static function getContent($path,$suffix)
    {
        $len = strlen($suffix);
        $files = scandir($path);
        $content = "";
        foreach ($files as $name)
        {
            if (in_array($name,array(".","..")))
            {
                continue;
            }

            if( substr($name,-$len) === $suffix )
            {
                $stream = fopen($path.$name, 'r');
                $content .= trim(stream_get_contents($stream))."\n";
                fclose($stream);
            }
        }
        return $content;
    }
    
    private static function getVersion($dir, $path, $suffixes, $type)
    { 
        $shouldBeCached = str_starts_with( $path, "/shared/" );
        $isCached = !empty($_SERVER["HTTP_REFERER"]);
        $cacheKey = "ressources:" . $dir;
        
        if( $shouldBeCached && $isCached )
        {
            $time = apcu_fetch($cacheKey);
            if( !empty($time) )
            {
                //error_log("cached");
                return $time;
            }
        }
        
        $time = Ressources::parseDir($dir, $suffixes, 0);
        if( $type == 'js' )
        {
            if( $path == "/main/" )
            {
                $dir = Ressources::prepareDir("components", $dir . '../' );
                $time = Ressources::parseDir($dir, ['.js','.json'], 0);
            }
            else
            {
                $i18n_file = Ressources::getI18NFile($dir);
                if( is_file( $i18n_file ) )
                {
                    $_time = filemtime($i18n_file);
                    if( $_time > $time ) $time = $_time;
                }
            }
        }
        
        if( $shouldBeCached )
        {
            //error_log("real");
            apcu_store($cacheKey, $time );
        }
        
        return $time;
    }

    private static function parseDir($dir, $suffixes, $time)
    {
        $files = scandir($dir);
        foreach ($files as $name)
        {
            if (in_array($name,array(".",".."))) continue;
            if( in_array( substr($name,strrpos($name,'.')), $suffixes ) )
            {
                $_time = filemtime($dir.$name);
                if( $_time > $time ) $time = $_time;
            }
        }
        return $time;
    }
    
    private static function prepareDir($type, $dir)
    {
        switch($type)
        {
          case 'css':
              $dir .= "css/";
              break;
          case 'js':
              $dir .= "js/";
              break;
          case 'components':
              $dir .= "components/";
              break;
        }
        
        return $dir;
    }

    private static function preparePath($type, $path, $suffixes)
    {
        $dir = __DIR__ . "/../.." . $path;
        $dir = Ressources::prepareDir($type, $dir);
        
        $version = Ressources::getVersion($dir, $path, $suffixes, $type);
        
        return "/shared/ressources/?type=" . $type . "&version=" . $version . "&path=" . urlencode($path);
    }

    private static function prepareModuleReadyName($path)
    {
        $func_name = [];
        $names = explode("/", trim($path,"/"));
        foreach( $names as $name )
        {
            if( empty($name) ) continue;

            $_parts = explode("_", $name);

            foreach( $_parts as $_part )
            {
                $func_name[] = ucfirst($_part);
            }
        }
        $func_name = implode("", $func_name);
        return "On" . $func_name . "Ready";
    }

    public static function getModule($path, $async=True)
    {
        $html = "";
        $dir = __DIR__ . "/../.." . $path;
        if( is_dir($dir."css/") ) $html .= '    <link href="' . Ressources::preparePath("css", $path, [".css"] ) . '" rel="stylesheet">'."\n";
        if( is_dir($dir."js/") ) $html .= '    <script' . ( $async ? " async": "" ) . ' src="' . Ressources::preparePath("js", $path, [".js"] ) . '"></script>'."\n";
        return $html;
    }

    public static function getModules($paths, $async=True)
    {
        $html = "<script>";
        $html .= "if(typeof mx === 'undefined') var mx = {};";
        $html .= "mx = {...mx, ...{ OnDocReadyWrapper: function(callback){ let args = []; let obj = [function(){ args.push(arguments); }, callback, args]; mx._OnDocReadyWrapper.push(obj); return function(){ obj[0](...arguments); }; }";
        $html .= ", _OnDocReadyWrapper: [], OnDocReady: [], OnScriptReady: [], OnReadyTrigger: function(){ mx.OnReadyCounter -= 1; }, OnReadyCounter: " . (count($paths) + 1);
        foreach ($paths as $path)
        {
            $html .= ", " . Ressources::prepareModuleReadyName($path) . ": []";
        }
        $html .= ", Translations: [] } };\n";
        $html .= "    </script>\n";
        $html .= Ressources::getModule("/shared/", $async);
        foreach ($paths as $path)
        {
            $html .= Ressources::getModule($path, $async);
        }

        return $html;
    }

    public static function build($type, $dir, $path)
    {
        $dir = Ressources::prepareDir($type, $dir);
      
        switch($type)
        {
          case 'css':
              return array( 'text/css; charset=utf-8', Ressources::getContent($dir,'.css') );

          case 'js':
              $content = Ressources::getContent($dir,'.js');
              if( $path == "/shared/" )
              {
                  $content .= '
                    mx._docReady = false;
                    mx.OnReadyTrigger();
                    mx.OnReadyTrigger = function() {
                        mx.OnReadyCounter -= 1;
                        if( mx.OnReadyCounter > 0 ) return;

                        for (var func of mx.OnScriptReady) { func(); }
                        mx.OnScriptReady = { push: function(func) { func(); } };

                        processDocReady();
                    }

                    function processDocReady()
                    {
                        if( mx.OnReadyCounter > 0 || !mx._docReady ) return;

                        for (var func of mx.OnDocReady) { func(); }
                        mx.OnDocReady = { push: function(func) { func(); } };

                        for(var wrapper of mx._OnDocReadyWrapper) {
                            for( var args of wrapper[2] ){ wrapper[1](...args) };
                            wrapper[0] = wrapper[1];
                        }
                    }

                    function triggerDocReady()
                    {
                        mx._docReady = true;
                        processDocReady();
                    }

                    if (document.readyState === "complete" || document.readyState === "interactive") triggerDocReady();
                    else document.addEventListener("DOMContentLoaded", triggerDocReady);';
              }
              else if( $path == "/main/" )
              {
                  $lang = Ressources::getLang();
                  $dir = Ressources::prepareDir("components", $dir . '../' );
                  $files = scandir($dir);
                  foreach ($files as $name)
                  {
                      if (in_array($name,array(".","..")))
                      {
                          continue;
                      }

                      if( substr($name,-3) === '.js' )
                      {
                          $stream = fopen($dir.$name, 'r');
                          $content .= stream_get_contents($stream);
                          fclose($stream);
                      }
                      else if( substr($name,-8) === '.' . $lang . '.json' )
                      {
                          $content .= Ressources::getI18NContent($dir.$name);
                      }
                  }
                  $content .= '
                    mx.OnReadyTrigger();';
              }
              else
              {
                  $ready_name = Ressources::prepareModuleReadyName($path);
                  $i18n_file = Ressources::getI18NFile($dir);
                  if( $i18n_file ) $content .= Ressources::getI18NContent($i18n_file);
                  $content .= '
                    mx.OnReadyTrigger();
                    for (var n in mx.' . $ready_name . ') { mx.' . $ready_name . '[n](); }
                    mx.' . $ready_name . ' = { push: function(func) { func(); } };';
              }
              return array( 'application/javascript; charset=utf-8', $content );
        }
    }
}
