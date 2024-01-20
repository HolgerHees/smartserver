<?php

class Preview {
    static $cache_map = array();

    private static function initFiles($camera_name)
    {
        if( !array_key_exists($camera_name, Preview::$cache_map) )
        {
            $camera_cache_directory = CACHE_DIRECTORY . $camera_name . "/";
            if( is_dir( $camera_cache_directory ) )
            {
                $images = array();
                foreach( scandir($camera_cache_directory) as $file )
                {
                    preg_match('/^(.+)_([a-z0-9]+)\.jpg+$/', $file, $matches);
                    if( !$matches ) continue;
                    $name =  $matches[1];
                    $type =  $matches[2];

                    if( !isset($images[$name]) ) $images[$name] = array();
                    $image_data = &$images[$name];

                    switch($type)
                    {
                        case "small":
                        case "medium":
                            $image_data[$type] = $file;
                            break;
                        default:
                            $image_data["original"] = $file;
                            $image_data["timestamp"] = $type;
                    }
                }

                Preview::$cache_map[$camera_name] = array_filter($images, function($image_data){ return count($image_data) == 4; } );
            }
        }
    }

    private static function generatePreview($img, $original_file, $preview_file, $preview_size, $timestamp)
    {
        if( $img == null )
        {
            $img = new Imagick;
            $img->readImage( $original_file );
            $img->setImageCompression(imagick::COMPRESSION_JPEG);

            $orgQuality = $img->getImageCompressionQuality();
            if( $orgQuality > 70 ) $img->setImageCompressionQuality(70);

        }

        if( $preview_size != null )
        {
            list( $width, $height ) = explode("x", $preview_size);
            $img->scaleImage( $width, $height, true );
        }

        file_put_contents($preview_file, $img->getImageBlob());
        touch($preview_file,$timestamp);
    }

    public static function getCount($camera_name)
    {
        if( !array_key_exists($camera_name, Preview::$cache_map) ) Preview::initFiles($camera_name);

        return count(Preview::$cache_map[$camera_name]);
    }

    public static function getFiles($camera_name)
    {
        if( !array_key_exists($camera_name, Preview::$cache_map) ) Preview::initFiles($camera_name);

        return Preview::$cache_map[$camera_name];
    }

    public static function check($original_file)
    {
        $path_parts = pathinfo($original_file);
        $camera_name = basename($path_parts["dirname"]);
        $camera_cache_directory = CACHE_DIRECTORY . $camera_name . "/";
        if( !is_dir( $camera_cache_directory ) ) mkdir( $camera_cache_directory, 0750, true );

        if( !array_key_exists($camera_name, Preview::$cache_map) ) Preview::initFiles($camera_name);

        $name = $path_parts["filename"];

        if( !isset(Preview::$cache_map[$camera_name][$name]) )
        {
            $org_cache_name = $path_parts["basename"];
            $org_lock_path = $camera_cache_directory . $name . ".lock";

            $fp = fopen( $org_lock_path, "c");
            if( flock($fp, LOCK_EX | LOCK_NB) )
            {
                if( is_file($org_lock_path) )
                {
                    echo "create " . $name . "\n";

                    $timestamp = filemtime($original_file);

                    $img = null;
                    $org_cache_path = $camera_cache_directory . $name . "_" . $timestamp . ".jpg" ;
                    if( !is_file( $org_cache_path ) ) $img = Preview::generatePreview($img, $original_file, $org_cache_path, null, $timestamp);

                    $medium_cache_path = $camera_cache_directory . $path_parts["filename"] . "_medium.jpg";
                    if( !is_file( $medium_cache_path ) ) $img = Preview::generatePreview($img, $original_file, $medium_cache_path, PREVIEW_MEDIUM_SIZE, $timestamp);

                    $small_cache_path = $camera_cache_directory . $path_parts["filename"] . "_small.jpg";
                    if( !is_file( $small_cache_path ) ) $img = Preview::generatePreview($img, $original_file, $small_cache_path, PREVIEW_SMALL_SIZE, $timestamp);

                    unlink($org_lock_path);
                }
                flock($fp, LOCK_UN);
            }
            fclose($fp);
        }
    }
}
