<?php
require "../shared/libs/ressources.php";
?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta name="viewport" content="height=device-height,
  width=device-width, initial-scale=1.0,
  minimum-scale=1.0, maximum-scale=1.0,
  user-scalable=no, target-densitydpi=device-dpi">
<?php echo Ressources::getModules(["/shared/mod/websocket/","/frigate/"]); ?>
<script>
var domain = location.host;
var init = mx.OnDocReadyWrapper(function(data){ mx.Video.build(document.querySelector("video"), "wss://frigate." + domain + "/live/mse/api/ws?src=streedside_main"); });
init();
</script>
</head>
<body>
<video muted playsinline width="80%"></video>
</body>
</html>
