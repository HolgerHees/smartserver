<?php
if( !isset($_GET['type']) ) exit;

function stream($path,$suffix)
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
    
switch($_GET['type'])
{
  case 'css':
      header('Content-Type: text/css; charset=utf-8');
      stream(__DIR__.'/main/css/','.css');
      break;

  case 'js':
      header('Content-Type: application/javascript; charset=utf-8');
      stream(__DIR__.'/main/js/','.js');
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

      $path = __DIR__.'/main/components/';
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
              echo "mx.Translations.push('".str_replace("\n","",stream_get_contents($stream))."');\n";
              fclose($stream);
          }
      }
      break;
}
?>
