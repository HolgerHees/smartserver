<?php

if( empty($_GET["url"]) || empty( $_GET['width'] ) || empty( $_GET['height'] ) )
{
  echo "missing parameter (url, width or height)";
  exit;
}

list($content, $time, $error_count) = getData( $_GET["url"] );

if( empty($content) )
{
	$content = fetchUrl( $_GET["url"], $error_count );
}
else
{
	if( empty($_GET['age']) || time() - $time > $_GET['age'] / 1000 )
	{
		//error_log($_GET["url"] . " 5");
		$_content = fetchUrl( $_GET["url"], $error_count );
		if( !empty( $_content ) )
		{
			$content = $_content;
		}
	}
}

if( $content )
{
    try {
        $imagick = new Imagick;

        $imagick->readImageBlob( $content );

        //$img->setImageCompression(imagick::COMPRESSION_JPEG);
        $imagick->setImageCompressionQuality(50); 
        
        $orgWidth = $imagick->getImageWidth();
        $orgHeight = $imagick->getImageHeight();

        $imagick->scaleImage( $_GET['width'], $_GET['height'], true );

        header("Content-Type: " . $imagick->getImageMimeType());

        echo $imagick->getImageBlob();
    }
    catch (ImagickException $e) 
    {
        http_response_code(503);
    }
}
else
{
    
    http_response_code(404);
}

function getData($url)
{
    $data = apcu_fetch( $url );
    $error_count = apcu_fetch( $url . ":error" );
    
    if( empty($data) )
    {
        return array(false, time(), $error_count);
    }
    
    list( $content, $time ) = $data;
    return array($content, $time, $error_count);
}

function fetchUrl( $url, $error_count )
{
	$c = curl_init();
	curl_setopt($c, CURLOPT_RETURNTRANSFER, 1);
	#$headers = array( 'Authorization: Basic '. $auth );
	#curl_setopt($c, CURLOPT_HTTPHEADER, $headers);
	curl_setopt($c, CURLOPT_URL, $url );
	$content = curl_exec($c);
	curl_close($c);	
	
	if( empty( $content ) )
    {
        if( $error_count > 1 ) error_log( $url . " had " . $error_count . " times not content" );
        apcu_store( $url . ":error", $error_count !== false ? $error_count + 1 : 1 );
	}
	else
	{
        apcu_store( $url, array( $content, time() ) );
        apcu_delete( $url . ":error" );
	}
	
	return $content;
}

