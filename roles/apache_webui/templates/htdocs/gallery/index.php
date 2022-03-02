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
    <link href="<?php echo Ressources::getCSSPath('/gallery/'); ?>" rel="stylesheet">

    <script>var mx = { OnScriptReady: [], OnDocReady: [] };</script>
    
    <script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
    <script src="<?php echo Ressources::getJSPath('/gallery/'); ?>"></script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame(null, "Gallery"); } );</script>
<?php
    include "inc/Image.php";
    include "inc/Folder.php";
    include "inc/Template.php";

    include "config.php";
    
    if( empty($_GET["sub"]) ) exit;
    $sub_folder = $_GET['sub'];
    
    $folder = new Folder($ftp_folder,$sub_folder);
    $images = $folder->getImages();
    
    list($width, $height, $type, $attr) = getimagesize($images[0]->getPath());
    
    $starttime = Template::getStarttime($images);
    $endtime = Template::getEndtime($images);
?>
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);

    mx.OnDocReady.push( function(){
        mx.Gallery.init(<?php echo $height; ?>,<?php echo $width; ?>,'<?php echo $sub_folder; ?>')
    });
</script>
<div class="slots"><?php echo Template::getSlots($starttime,$endtime,$images); ?></div>
<div id="gallery">
  <div class="layer"></div>
  <span class="button previous icon-left" onclick="mx.Gallery.jumpToPreviousImage()"></span>
  <span class="button next icon-right" onclick="mx.Gallery.jumpToNextImage()"></span>
  <span class="button close icon-cancel" onclick="mx.Gallery.closeDetails()"></span>
  <span class="button start icon-play" onclick="mx.Gallery.startPlay()"></span>
  <span class="button stop icon-stop" onclick="mx.Gallery.stopPlay()"></span>
<?php echo Template::getImages($images); ?>
</div>
</body>
</html>
