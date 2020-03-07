<?php
require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
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
    
    mx.UNCore = (function( ret ) {
    
        ret.openUrl = function(event,url)
        {
            event.stopPropagation();
            window.open(url);
        }
    
        return ret;
    })( mx.UNCore || {} );
</script>
<div class="table">
<?php
    if( file_exists($versions_state_file) )
    {
        $data = file_get_contents($versions_state_file);
        $data = json_decode($data);
        
        $states = $data->states;
        usort($states,function($a,$b)
        {
            return strcmp($a->name,$b->name);
        });
        
        $date = date_create($data->last_update);
        $date->setTimezone(new DateTimeZone('Europe/Berlin'));
        $last_update = $date->format("d.m.Y H:i");
    }
    else
    {
        $states = array();
        $last_update = "";
    }
?>
<div class="row">
<div><?php echo count($states); ?></div>
<div>Name</div>
<div>Version</div>
<div>Update</div>
<div>Upgrades</div>
<div><?php echo $last_update; ?></div>
</div>
<?php
    function formatVersion($version)
    {
        # git hashes
        if( strlen($version) > 20 ) return substr($version,0,7);
        
        return $version;
    }
    

    foreach( $states as $state)
    {
        $class = "green";
        if( count($state->upgrades) > 0 ) $class = "yellow";
        if( $state->update ) $class = "red";
        
        $update_class = $class == 'red' ? ' class="active"' : '';
        $upgrade_class = $class == 'yellow' ? ' class="active"' : '';
    
        switch($state->type)
        {
            case 'docker':
                $icon="icon-inbox";
                break;
            case 'github':
                $icon="icon-github";
                break;
            default:
                $icon="";
                break;
        }
    
        echo '<div class="row ' . $class . '">';
        echo '<div><span class="' . $icon . '"></span></div>';
        echo '<div>' . $state->name . '</div>';
        echo '<div>' . formatVersion($state->current->version) . '</div>';
        if( $state->update )
        {
            $updateHTML = '<div class="versionLink" onClick="mx.UNCore.openUrl(event,\'' .$state->update->url . '\')" ><span>' . formatVersion($state->update->version) . '</span><span class="icon-export"></span></div>';
        }
        else
        {
            $updateHTML = "";
        }
        echo '<div'.$update_class.'>' . $updateHTML . '</div>';
        if( count($state->upgrades) > 0)
        {
            $upgradesHTML_r = array();
            foreach( $state->upgrades as $upgrade)
            {
                $upgradesHTML_r[] = '<div class="versionLink" onClick="mx.UNCore.openUrl(event,\'' .$upgrade->url . '\')" ><span>' . formatVersion($upgrade->version) . '</span><span class="icon-export"></span></div>';
            }
            $upgradesHTML = implode(", ",$upgradesHTML_r);
        }
        else
        {
            $upgradesHTML = "";
        }
        echo '<div'.$upgrade_class.'>' . $upgradesHTML . '</div>';
        
        $date = date_create($state->last_update);
        $date->setTimezone(new DateTimeZone('Europe/Berlin'));
        $last_update = $date->format("d.m.Y H:i");

        echo '<div>' . $last_update . '</div>';
        echo '</div>';
    }
?>
</div>
</body>
</html>
