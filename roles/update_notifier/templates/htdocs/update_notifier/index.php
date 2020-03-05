<?php
require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./css/index.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="/ressources?type=js"></script>
<script>
function initPage()
{
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body>
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
</script>
<div class="table">
<div class="row">
<div></div>
<div>Name</div>
<div>Version</div>
<div>Update</div>
<div>Upgrades</div>
</div>
<?php
    $data = file_get_contents($versions_state_file);
    $versions = json_decode($data);
    
    foreach( $versions as $version)
    {
        $class = "green";
        if( count($version->upgrades) > 0 ) $class = "yellow";
        if( $version->update ) $class = "red";
        
        $update_class = $class == 'red' ? ' class="active"' : '';
        $upgrade_class = $class == 'yellow' ? ' class="active"' : '';
    
        echo '<div class="row ' . $class . '">';
        echo '<div></div>';
        echo '<div>' . $version->name . '</div>';
        echo '<div>' . $version->current . '</div>';
        echo '<div'.$update_class.'>' . $version->update . '</div>';
        echo '<div'.$upgrade_class.'>' . implode( ", ", $version->upgrades ) . '</div>';
        echo '</div>';
    }
?>
</div>
</body>
</html>
