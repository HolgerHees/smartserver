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

                    $index = strpos($file, "_small.jpg");
                    if( $index !== false )
                    {
                        $name = substr($file,0,$index);
                        if( !isset($images[$name]) ) $images[$name] = array(null,null,$file);
                        else $images[$name][2] = $file;
                    }
                    else
                    {
                        $index = strpos($file, "_medium.jpg");
                        if( $index !== false )
                        {
                            $name = substr($file,0,$index);
                            if( !isset($images[$name]) ) $images[$name] = array(null,$file,null);
                            else $images[$name][1] = $file;
                        }
                        else
                        {
                            $index = strpos($file, ".");
                            if( $index !== false )
                            {
                                $name = substr($file,0,$index);
                                if( !isset($images[$name]) ) $images[$name] = array($file,null,null);
                                else $images[$name][0] = $file;
                            }
                        }
                    }
                }
                Preview::$cache_map[$camera_name] = $images;
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
        touch($preview_file, $timestamp);
    }

    public static function getCount($camera_name)
    {
        if( !array_key_exists($camera_name, Preview::$cache_map) ) Preview::initFiles($camera_name);

        return count(Preview::$cache_map[$camera_name]);
    }

    public static function getFiles($camera_name)
    {
        if( !array_key_exists($camera_name, Preview::$cache_map) ) Preview::initFiles($camera_name);

        $files = array();
        foreach( Preview::$cache_map[$camera_name] as $data )
        {
            if( $data[0] == null || $data[1] == null || $data[2] == null ) continue;

            $files[] = $data;
        }

        return $files;
    }

    public static function check($original_file)
    {
        $path_parts = pathinfo($original_file);
        $camera_name = basename($path_parts["dirname"]);
        $camera_cache_directory = CACHE_DIRECTORY . $camera_name . "/";
        if( !is_dir( $camera_cache_directory ) ) mkdir( $camera_cache_directory, 0750, true );

        if( !array_key_exists($camera_name, Preview::$cache_map) ) Preview::initFiles($camera_name);

        $name = $path_parts["filename"];

        if( !isset(Preview::$cache_map[$camera_name][$name]) || Preview::$cache_map[$camera_name][$name][0] == null || Preview::$cache_map[$camera_name][$name][1] == null || Preview::$cache_map[$camera_name][$name][2] == null )
        {
            $org_cache_name = $path_parts["basename"];
            $org_cache_path = $camera_cache_directory . $org_cache_name;

            $fp = fopen( $org_cache_path.".lock", "c");
            if( flock($fp, LOCK_EX | LOCK_NB) )
            {
                if( is_file($org_cache_path.".lock") )
                {
                    echo "create " . $name . "\n";

                    $timestamp = filemtime($original_file);

                    $medium_cache_name = $path_parts["filename"] . "_medium.jpg";
                    $small_cache_name = $path_parts["filename"] . "_small.jpg";

                    $small_cache_path = $camera_cache_directory . $small_cache_name;
                    $medium_cache_path = $camera_cache_directory . $medium_cache_name;

                    if( !is_file( $org_cache_path ) )
                    {
                        copy($original_file, $org_cache_path);
                        touch($org_cache_path, $timestamp);
                    }

                    $img = null;
                    if( !is_file( $medium_cache_path ) ) $img = Preview::generatePreview($img, $original_file, $medium_cache_path, PREVIEW_MEDIUM_SIZE, $timestamp);
                    if( !is_file( $small_cache_path ) ) $img = Preview::generatePreview($img, $original_file, $small_cache_path, PREVIEW_SMALL_SIZE, $timestamp);

                    unlink($org_cache_path.".lock");
                }
                flock($fp, LOCK_UN);
            }
            fclose($fp);
        }
    }
}
