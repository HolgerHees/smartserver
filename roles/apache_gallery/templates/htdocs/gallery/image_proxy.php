<?php
if( empty($_GET["url"]) )
{
  echo "missing parameter (url)";
  exit;
}

$url = $_GET["url"];
$auth = empty($_GET['user']) || empty($_GET['password']) ? null : base64_encode( $_GET['user']. ":" . $_GET['password'] );


$age = empty($_GET['age']) ? 1000 : $_GET['age'];

list($content, $mime, $time, $error_count) = getData( $url, $age, $auth );

if( $content )
{
    try {
        if( !empty( $_GET['width'] ) && empty( $_GET['height'] ) )
        {
            list( $content, $mime ) = scaleImage( $content, $_GET['width'], $_GET['height'], true );
        }

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
    fetchError();
}

function fetchError()
{
    $url = str_replace($_SERVER['REDIRECT_SCRIPT_URL'], "/_fallback/cam.jpg", $_SERVER['REDIRECT_SCRIPT_URI']);

    list($content, $mime, $time, $error_count) = getData( $url, 60000, null );

    header("Content-Type: " . $mime);
    echo $content;
}

function getData($url, $age, $auth)
{
    list($content, $mime, $time, $error_count) = fetchData( $url );
    if( empty($content) || time() - $time > $age / 1000 )
    {
        list( $_content, $_mime ) = fetchUrl( $url, $auth, $error_count );
        if( !empty($_content) )
        {
            $content = $_content;
            $mime = $_mime;
        }
    }

    return array( $content, $mime, $time, $error_count );
}

function fetchData($url)
{
    $data = apcu_fetch( $url );
    $error_count = apcu_fetch( $url . ":error" );
    
    if( empty($data) )
    {
        return array(false, time(), $error_count);
    }
    
    list( $content, $mime, $time ) = $data;
    return array($content, $mime, $time, $error_count);
}

function fetchUrl( $url, $auth, $error_count )
{
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
        if( $error_count > 1 ) error_log( $url . " had " . $error_count . " times not content" );
        apcu_store( $url . ":error", $error_count !== false ? $error_count + 1 : 1 );
	}
	else
	{
        apcu_store( $url, array( $content, $mime, time() ) );
        apcu_delete( $url . ":error" );
	}
	
	return array( $content, $mime );
}

/*function streamUrl( $url, $auth )
{
    $c = initCurl($url, $auth);

    curl_setopt($c, CURLOPT_WRITEFUNCTION, 'streamCallback');

    $boundaryOut = "MyMultipartBoundaryDoNotStumble";
    header("Content-Type: multipart/x-mixed-replace; boundary=$boundaryOut");
    echo "--$boundaryOut\r\n";

    curl_exec($c);
    curl_close($c);

    return False;
}

function streamCallback($curl, $data) {
    // Process the received data
    echo $data;

    // Return the length of the data processed
    return strlen($data);
}*/

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
    $imagick->setImageCompressionQuality(50);

    $orgWidth = $imagick->getImageWidth();
    $orgHeight = $imagick->getImageHeight();

    if( $force || $orgWidth > $width || $orgHeight > $height )
    {
        $imagick->scaleImage( $width, $height, true );
    }

    return array( $imagick->getImageBlob(), $imagick->getImageMimeType() );
}
