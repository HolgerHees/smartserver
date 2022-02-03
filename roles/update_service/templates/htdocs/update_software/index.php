<?php
require "config.php";

require "../shared/libs/http.php";
require "../shared/libs/auth.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
<link rel="stylesheet" href="/main/css/shared_root.css">
<link rel="stylesheet" href="/main/css/shared_ui.css">
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
<body class="inline">
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
<div class="form table">
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
<div>Updates</div>
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
        if( count($state->updates) > 0 )
        {
            $class = "yellow";
            foreach( $state->updates as $update)
            {
                if( $state->current->branch == $update->branch )
                {
                    $class = "red";
                    break;
                }
            }
        }
    
        switch($state->type)
        {
            case 'docker':
                $icon="icon-inbox";
                break;
            case 'github':
                $icon="icon-git";
                break;
            case 'opensuse':
            case 'fedora':
                $icon="icon-desktop";
                break;
            default:
                $icon="";
                break;
        }
    
        echo '<div class="row ' . $class . '">';
        echo '<div class="typeLink" onClick="mx.UNCore.openUrl(event,\'' .$state->url . '\')"><span class="' . $icon . '"></span></div>';
        echo '<div>' . $state->name . '</div>';

        $latest_date = date_create($state->current->date);
        $date = $latest_date->format("d.m.Y H:i");

        echo '<div class="tooltip">' . formatVersion($state->current->version) . ' <span class="hover">Version ' . formatVersion($state->current->version) . ' from ' . $date . '</span></div>';
        
        if( count($state->updates) > 0)
        {
            $updates = $state->updates;
            usort($updates,function($a,$b)
            {
                return strcmp($a->version,$b->version);
            });
            
            $latest_date = null;
            $upgradesHTML_r = array();
            foreach( $updates as $update)
            {
                #error_log($update->date);

                $date = date_create($update->date);
                if( !$date )
                {
                    $date = date_create(explode(".",$update->date)[0]);
                }
                #error_log($date);
                
                if( $latest_date == null or $latest_date < $date ) $latest_date = $date;

                $current_branch = $state->current->branch == $update->branch;
                
                if( $update->url )
                {
                    $upgradesHTML_r[] = '<div class="versionLink' . ( $current_branch ? ' currentBranch' : '' ) . '" onClick="mx.UNCore.openUrl(event,\'' .$update->url . '\')" ><span>' . formatVersion($update->version) . '</span><span class="icon-export"></span></div>';
                }
                else
                {
                    $upgradesHTML_r[] = '<div class="' . ( $current_branch ? 'currentBranch' : '' ) . '"><span>' . formatVersion($update->version) . '</span></div>';
                }
            }
            $upgradesHTML = implode(", ",$upgradesHTML_r);
            
            $now = new DateTime();
            $diff = $latest_date->diff($now);
            
            $day_diff = $diff->days;
            $now_minutes = $now->format("H") * 60 + $now->format("i");
            $latest_minutes = $latest_date->format("H") * 60 + $latest_date->format("i");
            if( $now_minutes < $latest_minutes )
            {
                $day_diff++;
            }
            
            if( $day_diff <= 1)
            {
                $last_update = ( $day_diff == 0 ? 'Today' : 'Yesterday' ) . ' ' . $latest_date->format("H:i");
            }
            else
            {
                if( $day_diff > 30 )
                {
                    $last_update = $latest_date->format("d.m.Y");
                }
                else
                {
                    $last_update = $day_diff . ' days ago';
                }
            }
            
            $last_update = '<span class="default">' . $last_update . '</span>';
            $last_update_details = '<span class="hover">' . $latest_date->format("d.m.Y H:i") . '</span>';
        }
        else
        {
            $upgradesHTML = "";
            $last_update = "";
            $last_update_details = "";
        }
        echo '<div>' . $upgradesHTML . '</div>';
        
        #$date = date_create($state->last_update);
        #$date->setTimezone(new DateTimeZone('Europe/Berlin'));
        #$last_update = $date->format("d.m.Y H:i");

        echo '<div class="tooltip">' . $last_update . $last_update_details . '</div>';
        
        echo '</div>';
    }
?>
</div>
</body>
</html>
