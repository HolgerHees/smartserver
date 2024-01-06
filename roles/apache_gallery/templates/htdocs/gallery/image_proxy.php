<?php
if( empty($_GET["url"]) )
{
  echo "missing parameter (url)";
  exit;
}

$url = $_GET["url"];
$auth = empty($_GET['user']) || empty($_GET['password']) ? null : base64_encode( $_GET['user']. ":" . $_GET['password'] );


$age = empty($_GET['age']) ? 1000 : $_GET['age'];

list($content, $mime, $time) = getData( $url, $age, $auth );

if( $content )
{
    try {
        if( !empty( $_GET['width'] ) && $_GET['width'] > 0 && !empty( $_GET['height'] ) && $_GET['height'] > 0 )
        {
            list( $content, $mime ) = scaleImage( $content, $_GET['width'], $_GET['height'], true );
        }

        header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
        header("Cache-Control: post-check=0, pre-check=0", false);
        header("Pragma: no-cache");
        header("Content-Type: " . $mime);
        echo $content;
    }
    catch (ImagickException $e)
    {
        http_response_code(503);
    }
}
else
{
    $url = str_replace($_SERVER['REDIRECT_SCRIPT_URL'], "/_fallback/cam.jpg", $_SERVER['REDIRECT_SCRIPT_URI']);

    list($content, $mime, $time) = getData( $url, 60000, null );

    header("Content-Type: " . $mime);
    echo $content;
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
                $content = apcu_fetch( $url . ":content" );
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
    apcu_store( $url . ":fetch", 1 );

    $c = initCurl($url, $auth);

    #$start = microtime(true);
    $content = curl_exec($c);
    #$end = microtime(true);

    #error_log($end - $start);
    $size = curl_getinfo($c, CURLINFO_CONTENT_LENGTH_DOWNLOAD );
    #error_log("fetched size " . $size);
    #error_log("calculated size " . strlen($content));

    list( $content, $mime ) = scaleImage( $content, 1920, 1080, false );

    #$mime = curl_getinfo($c, CURLINFO_CONTENT_TYPE);

	curl_close($c);	

    if( empty( $content ) )
    {
        $error_count = apcu_fetch( $url . ":error" );
        if( $error_count > 1 ) error_log( $url . " had " . $error_count . " times not content" );
        apcu_store( $url . ":error", $error_count !== false ? $error_count + 1 : 1 );
	}
	else
	{
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
        $headers = array( 'Authorization: Basic '. $auth );
        curl_setopt($c, CURLOPT_HTTPHEADER, $headers);
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
