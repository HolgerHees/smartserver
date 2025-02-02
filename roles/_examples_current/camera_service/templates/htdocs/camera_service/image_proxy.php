<?php
if( empty($_GET["url"]) )
{
  echo "missing parameter (url)";
  exit;
}

register_shutdown_function( "fatal_handler" );

$url = $_GET["url"];
$auth = empty($_GET['user']) || empty($_GET['password']) ? null : ( $_GET['user']. ":" . $_GET['password'] );


$age = empty($_GET['age']) ? 1000 : $_GET['age'];

list($content, $mime, $time) = getData( $url, $age, $auth );

header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");

if( $content )
{
    try {
        if( !empty( $_GET['width'] ) && $_GET['width'] > 0 && !empty( $_GET['height'] ) && $_GET['height'] > 0 )
        {
            list( $content, $mime ) = scaleImage( $content, $_GET['width'], $_GET['height'], true );
        }

        header("Content-Type: " . $mime);
        echo $content;
    }
    catch (ImagickException $e)
    {
        header("Content-Type: text/plain");
        http_response_code(503);

    }
}
else
{
    header("Content-Type: text/plain");
    http_response_code(504);
}

exit(0);

function fatal_handler() {
    global $url;

    # cleanup
    #error_log("cleanup");
    apcu_delete( $url . ":fetch" );
}

function getData($url, $age, $auth)
{
    $meta = apcu_fetch( $url . ":meta" );
    list( $mime, $time ) = empty($meta) ? array(null, -1) : $meta;
    if( $time == -1 || time() - $time > $age / 1000 )
    {
        $recheck = 0;
        while( apcu_fetch( $url . ":fetch" ) )
        {
            usleep(50000);
            $recheck += 1;
        }
        if( $recheck > 0 )
        {
            //error_log("delayed reuse " . $recheck . " " . $url);
            $content = apcu_fetch( $url . ":content" );
        }
        else
        {
            //error_log("fetch " . $url);
            list( $_content, $_mime ) = fetchUrl( $url, $auth );
            if( !empty($_content) )
            {
                $content = $_content;
                $mime = $_mime;
            }
            else
            {
                $content = "";
            }
        }
    }
    else
    {
        //error_log("reuse " . $url);
        $content = apcu_fetch( $url . ":content" );
    }

    return array($content, $mime, $time);
}

function fetchUrl( $url, $auth )
{
    apcu_store( $url . ":fetch", 1, 120 );

    $c = initCurl($url, $auth);

    #$start = microtime(true);
    $content = curl_exec($c);
    #$end = microtime(true);

    #error_log($end - $start);
    $size = curl_getinfo($c, CURLINFO_CONTENT_LENGTH_DOWNLOAD );
    #error_log("fetched size " . $size);
    #error_log("calculated size " . strlen($content));

    #$mime = curl_getinfo($c, CURLINFO_CONTENT_TYPE);

    $return_code =  curl_getinfo($c, CURLINFO_HTTP_CODE);

	curl_close($c);

    if( empty( $content ) || $return_code != 200 )
    {
        $error_count = apcu_fetch( $url . ":error" );
        if( $return_code != 200 ) error_log( $url . " had response code " . $return_code );
        elseif( $error_count > 1 ) error_log( $url . " had " . $error_count . " times not content" );
        apcu_store( $url . ":error", $error_count !== false ? $error_count + 1 : 1 );

        $content = "";
        $mime = "";
	}
	else
	{
        list( $content, $mime ) = scaleImage( $content, 1920, 1080, false );

        apcu_store( $url . ":meta", array( $mime, time() ) );
        apcu_store( $url . ":content", $content );
        apcu_delete( $url . ":error" );
	}

    apcu_delete( $url . ":fetch" );

    return array( $content, $mime );
}

function initCurl( $url, $auth )
{
    $c = curl_init($url);

    if( strpos($url, "https") === 0 )
    {
        curl_setopt($c, CURLOPT_SSL_VERIFYHOST, 0);
        curl_setopt($c, CURLOPT_SSL_VERIFYPEER, 0);
    }

    if( !empty($auth) )
    {
        curl_setopt($c, CURLOPT_HTTPAUTH, CURLAUTH_ANY );
        curl_setopt($c, CURLOPT_USERPWD, $auth );
    }
    curl_setopt($c, CURLOPT_RETURNTRANSFER, true);

    return $c;
}

function scaleImage( $image, $width, $height, $force )
{
    $imagick = new Imagick;
    $imagick->readImageBlob( $image );
    //$img->setImageCompression(imagick::COMPRESSION_JPEG);

    $orgQuality = $imagick->getImageCompressionQuality();
    if( $orgQuality > 70 ) $imagick->setImageCompressionQuality(70);

    $orgWidth = $imagick->getImageWidth();
    $orgHeight = $imagick->getImageHeight();

    //if( $force || $orgWidth > $width || $orgHeight > $height )
    if( $orgWidth > $width || $orgHeight > $height )
    {
        $imagick->scaleImage( $width, $height, true );
    }

    return array( $imagick->getImageBlob(), $imagick->getImageMimeType() );
}
