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
    <link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
    <link href="<?php echo Ressources::getCSSPath('/camera_service/'); ?>" rel="stylesheet">
    <script>var mx = { OnScriptReady: [], OnDocReady: [] };</script>
    <script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
    <script src="<?php echo Ressources::getJSPath('/camera_service/'); ?>"></script>
    <script src="/shared/js/socketio/socket.io.min.js"></script>
    <script src="<?php echo Ressources::getComponentPath('/camera_service/'); ?>"></script>
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
        function handleErrors()
        {
            mx.Error.handleError( mx.I18N.get( "Service is currently not available") );
        }
        const socket = io("/", {path: '/camera_service/api/socket.io' });
        socket.on('connect', function() {
            mx.Error.confirmSuccess();
            socket.emit('init', camera_name);
        });
        socket.on('init', data => mx.Gallery.init(data));
        socket.on('change_' + camera_name, data => mx.Gallery.update(data));
        socket.on('connect_error', err => handleErrors(err))
        socket.on('connect_failed', err => handleErrors(err))
        socket.on('disconnect', err => handleErrors(err))
    });
</script>
<div class="contentLayer error"></div>
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
