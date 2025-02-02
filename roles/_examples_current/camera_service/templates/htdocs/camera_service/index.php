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
<?php echo Ressources::getModules(["/shared/mod/websocket/","/camera_service/"]); ?>
<script>
const params = new URLSearchParams(window.location.search);
const camera_name = params.get("sub");

var initData = mx.OnDocReadyWrapper(function(data){ mx.Gallery.init(data); });
var updateData = mx.OnDocReadyWrapper(function(data){ mx.Gallery.update(data); });

mx.OnSharedModWebsocketReady.push(function(){
    let socket = mx.ServiceSocket.init('camera_service', camera_name);
    socket.on("init", (data) => initData(data));
    socket.on("update", (data) => updateData(data));
});

</script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame(null, "Gallery"); } );</script>
<script>
</script>
<div class="slots"></div>
<div id="gallery">
  <div class="layer"></div>
  <span class="button next icon-left" onclick="mx.Gallery.jumpToNextImage(event)"></span>
  <span class="button previous icon-right" onclick="mx.Gallery.jumpToPreviousImage(event)"></span>
  <span class="button close icon-cancel" onclick="mx.Gallery.closeDetails(event)"></span>
  <span class="button play icon-play" onclick="mx.Gallery.tooglePlay(event)"></span>
</div>
</body>
</html>
