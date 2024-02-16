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

    public static function getModule($path)
    {
        $html = "";
        $dir = __DIR__ . "/../.." . $path;
        if( is_dir($dir."css/") ) $html .= '    <link href="' . Ressources::preparePath("css", $path, [".css"] ) . '" rel="stylesheet">'."\n";
        if( is_dir($dir."js/") ) $html .= '    <script src="' . Ressources::preparePath("js", $path, [".js"] ) . '"></script>'."\n";
        return $html;
    }

    public static function getModules($paths)
    {
        $html = "<script>
        if(typeof mx === 'undefined') var mx = {};
        mx = {...mx, ...{ OnScriptReady: [], OnDocReady: [], Translations: [] } };\n";
        $html .= "    </script>\n";
        $html .= Ressources::getModule("/shared/");
        foreach ($paths as $path)
        {
            $html .= Ressources::getModule($path);
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
                    for (var n in mx.OnScriptReady) {
                        mx.OnScriptReady[n].call();
                    }

                    mx.OnScriptReady = {
                        push: function(func) {
                            func.call();
                        }
                    };

                    if (document.readyState === "complete" || document.readyState === "interactive")
                    {
                        mx.Core.OnDocReady();
                    }
                    else
                    {
                        document.addEventListener("DOMContentLoaded", mx.Core.OnDocReady);
                    }';
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
              }
              else
              {
                  $i18n_file = Ressources::getI18NFile($dir);
                  if( $i18n_file ) $content .= Ressources::getI18NContent($i18n_file);
              }
              return array( 'application/javascript; charset=utf-8', $content );
        }
    }
}
