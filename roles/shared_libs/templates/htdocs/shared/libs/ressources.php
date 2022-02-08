<?php
class Ressources
{
    private static function stream($path,$suffix)
    {
        $len = strlen($suffix);
        $files = scandir($path);
        foreach ($files as $name)
        {
            if (in_array($name,array(".","..")))
            {
                continue;
            }

            if( substr($name,-$len) === $suffix )
            {
                $stream = fopen($path.$name, 'r');
                echo stream_get_contents($stream);
                fclose($stream);
            }
        }
    }
    
    private static function getVersion($dir,$path,$suffixes)
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
        
        $files = scandir($dir);
        $time = 0;
        foreach ($files as $name)
        {
            if (in_array($name,array(".","..")))
            {
                continue;
            }

            if( in_array( substr($name,strrpos($name,'.')), $suffixes ) )
            {
                $_time = filemtime($dir.$name);
                if( $_time > $time ) $time = $_time;
            }
        }
        
        if( $shouldBeCached )
        {
            //error_log("real");
            apcu_store($cacheKey, $time );
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
        
        $version = Ressources::getVersion($dir,$path,$suffixes);
        
        return "/shared/ressources/?type=" . $type . "&version=" . $version . "&path=" . urlencode($path);
    }

    public static function getJSPath($path)
    {
        return Ressources::preparePath("js", $path, [".js"] );
    }
  
    public static function getCSSPath($path)
    {
        return Ressources::preparePath("css", $path, [".css"] );
    }

    public static function getComponentPath($path)
    {
        $dir = __DIR__ . "/../.." . $path;
        $dir = Ressources::prepareDir("components", $dir);
        
        return Ressources::preparePath("components", $path, ['.js','.json'] );
    }
   
    public static function dump($type, $dir, $path)
    {
        $dir = Ressources::prepareDir($type, $dir);
      
        switch($type)
        {
          case 'css':
              header('Content-Type: text/css; charset=utf-8');
              Ressources::stream($dir,'.css');
              break;

          case 'js':
              header('Content-Type: application/javascript; charset=utf-8');
              Ressources::stream($dir,'.js');
              if( str_starts_with( $path, "/shared/" ) )
              {
                  echo '
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
              break;
              
          case 'components':
              header('Content-Type: application/javascript; charset=utf-8');

              $lang = isset($_SERVER['HTTP_ACCEPT_LANGUAGE']) ? $_SERVER['HTTP_ACCEPT_LANGUAGE'] : "";

              if( strpos($lang,"de") !== false )
              {
                  $lang = 'de';
              }
              else
              {
                  $lang = '';
              }

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
                      echo stream_get_contents($stream);
                      fclose($stream);
                  }
                  else if( substr($name,-8) === '.' . $lang . '.json' )
                  {
                      $stream = fopen($dir.$name, 'r');
                      $content = stream_get_contents($stream);
                      $content = str_replace("'","\\'",$content);
                      $content = str_replace("\n","",$content);
                      echo "mx.Translations.push('".$content."');\n";
                      fclose($stream);
                  }
              }
              break;
        }
    }
}
