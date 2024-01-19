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
    
    $folder = new Folder($sub_folder);
    $images = $folder->getImages();
    
    if( count($images) == 0 )
    {
        $width = 0;
        $height = 0;
        $starttime = new DateTime();
        $endtime = $starttime;
    }
    else
    {
        list($width, $height, $type, $attr) = getimagesize(CACHE_DIRECTORY.$images[0]->getSubFolder()."/".$images[0]->getOriginalCacheName());

        $starttime = Template::getStarttime($images);
        $endtime = Template::getEndtime($images);
    }
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
  <span class="button next icon-left" onclick="mx.Gallery.jumpToNextImage(event)"></span>
  <span class="button previous icon-right" onclick="mx.Gallery.jumpToPreviousImage(event)"></span>
  <span class="button close icon-cancel" onclick="mx.Gallery.closeDetails(event)"></span>
  <span class="button start icon-play" onclick="mx.Gallery.startPlay(event)"></span>
  <span class="button stop icon-stop" onclick="mx.Gallery.stopPlay(event)"></span>
<?php echo Template::getImages($images); ?>
</div>
</body>
</html>
