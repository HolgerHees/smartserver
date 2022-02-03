<?php
class Ressources
{
    public static function getCSSVersion($path)
    {
        return Ressources::getVersion($path,['.css']);
    }

    public static function getJSVersion($path)
    {
        return Ressources::getVersion($path,['.js']);
    }

    public static function getComponentVersion($path)
    {
        return Ressources::getVersion($path,['.js','*.json']);
    }
  
    public static function getVersion($path,$suffixes)
    {
        $files = scandir($path);
        $time = 0;
        foreach ($files as $name)
        {
            if (in_array($name,array(".","..")))
            {
                continue;
            }

            if( in_array( substr($name,strpos($name,'.')), $suffixes ) )
            {
                $_time = filemtime($path.$name);
                if( $_time > $time ) $time = $_time;
            }
        }
        
        return $time;
    }

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
    
    public static function dump($type, $base_folder, $is_main = false)
    {
            
        switch($type)
        {
          case 'css':
              header('Content-Type: text/css; charset=utf-8');
              Ressources::stream($base_folder.'/css/','.css');
              break;

          case 'js':
              header('Content-Type: application/javascript; charset=utf-8');
              Ressources::stream($base_folder.'/js/','.js');
              if( $is_main )
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

              $path = $base_folder.'/components/';
              $files = scandir($path);
              foreach ($files as $name)
              {
                  if (in_array($name,array(".","..")))
                  {
                      continue;
                  }

                  if( substr($name,-3) === '.js' )
                  {
                      $stream = fopen($path.$name, 'r');
                      echo stream_get_contents($stream);
                      fclose($stream);
                  }
                  else if( substr($name,-8) === '.' . $lang . '.json' )
                  {
                      $stream = fopen($path.$name, 'r');
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
