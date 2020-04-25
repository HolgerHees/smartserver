<?php

if( empty($_GET["url"]) || empty( $_GET['width'] ) || empty( $_GET['height'] ) )
{
  echo "missing parameter (url, width or height)";
  exit;
}

$data = apcu_fetch( $_GET["url"] );

//error_log( $_GET["url"] . " 1");

if( empty($data) )
{
	//error_log($_GET["url"] . " 2");
	$content = fetchUrl( $_GET["url"] );
	if( !empty( $content ) )
	{
		//error_log($_GET["url"] . " 3");
		$data = array( $content, time() );
		apcu_store( $_GET["url"], $data );
	}
}
else
{
	//error_log($_GET["url"] . " 4");
	list( $content, $time ) = $data;
	//error_log(print_r($data,true) );
	
	if( empty($_GET['age']) || time() - $time > $_GET['age'] / 1000 )
	{
		//error_log($_GET["url"] . " 5");
		$_content = fetchUrl( $_GET["url"] );
		if( !empty( $_content ) )
		{
			//error_log($_GET["url"] . " 6");
			$data = array( $_content, time() );
			apcu_store( $_GET["url"], $data );
			
			$content = $_content;
		}
	}
	else
	{
		//error_log("get cached data");
	}
}

if( $content )
{
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
else
{
    
    http_response_code(404);
}

function fetchUrl( $url )
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
		error_log( $url . " has no content");
	}
	
	return $content;
}

