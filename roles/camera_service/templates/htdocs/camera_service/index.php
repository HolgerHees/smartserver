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
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame(null, "Gallery"); } );</script>
<?php
    if( empty($_GET["sub"]) ) exit;
    $sub_folder = $_GET['sub'];
?>
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
    var camera_name = "<?php echo $sub_folder; ?>";

    mx.OnDocReady.push( function(){
        let socket = mx.ServiceSocket.init('camera_service');
        socket.on("connect", (socket) => socket.emit('init', camera_name));
        socket.on("init", (data) => mx.Gallery.init(data));
        socket.on("change_" + camera_name, (data) => mx.Gallery.update(data));
    });
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
