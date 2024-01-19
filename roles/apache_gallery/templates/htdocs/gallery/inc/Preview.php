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
                    if( $file == "." || $file == ".." || strpos($file, ".lock") !== false ) continue;

                    $index = strrpos($file, ".");
                    if( $index === false ) continue;

                    $filename = substr($file,0,$index);

                    $index = strrpos($filename, "_");
                    if( $index === false ) continue;

                    $name = substr($filename,0,$index);
                    $type = substr($filename,$index + 1);

                    if( !isset($images[$name]) ) $images[$name] = array(null,null,null,null);
                    $image_data = &$images[$name];

                    switch($type)
                    {
                        case "small":
                            $image_data[2] = $file;
                            break;
                        case "medium":
                            $image_data[1] = $file;
                            break;
                        default:
                            $image_data[0] = $file;
                            $image_data[4] = $type;
                    }
                }

                Preview::$cache_map[$camera_name] = array_filter($images, function($image_data){ return $image_data[0] != null && $image_data[1] != null && $image_data[2] != null; } );;
            }
        }
    }

    private static function generatePreview($img, $original_file, $preview_file, $preview_size, $timestamp)
    {
        list( $width, $height ) = explode("x", $preview_size);

        if( $img == null )
        {
            $img = new Imagick;
            $img->readImage( $original_file );
            $img->setImageCompression(imagick::COMPRESSION_JPEG);

            $orgQuality = $img->getImageCompressionQuality();
            if( $orgQuality > 70 ) $img->setImageCompressionQuality(70);

        }

        $img->scaleImage( $width, $height, true );

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

        return array_values(Preview::$cache_map[$camera_name]);
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
                    $org_cache_path = $camera_cache_directory . $name . "_" . $timestamp . "." . $path_parts["extension"] ;

                    if( !is_file( $org_cache_path ) )
                    {
                        copy($original_file, $org_cache_path);
                        touch($org_cache_path,$timestamp);
                    }

                    $img = null;
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
