<?php

class Preview {
    static $cache_map = array();

    public static function check($original_file)
    {
        $path_parts = pathinfo($original_file);
        $camera_name = basename($path_parts["dirname"]);
        $camera_cache_directory = CACHE_DIRECTORY . $camera_name . "/";

        if( !array_key_exists($camera_name, Preview::$cache_map) )
        {
            if( !is_dir( $camera_cache_directory ) ) mkdir( $camera_cache_directory, 0750, true );

            Preview::$cache_map[$camera_name] = scandir($camera_cache_directory);
        }

        $small_cache_name = $path_parts["filename"] . "_small.jpg";
        $medium_cache_name = $path_parts["filename"] . "_medium.jpg";
        $org_cache_name = $path_parts["basename"];

        if( !in_array($small_cache_name, Preview::$cache_map[$camera_name] ) || !in_array($medium_cache_name, Preview::$cache_map[$camera_name] ) || !in_array($org_cache_name, Preview::$cache_map[$camera_name] ) )
        {
            Preview::processFile($camera_cache_directory, $original_file, $small_cache_name, $medium_cache_name, $org_cache_name);

            if( !in_array($small_cache_name, Preview::$cache_map[$camera_name] ) ) array_push(Preview::$cache_map[$camera_name],$small_cache_name);
            if( !in_array($medium_cache_name, Preview::$cache_map[$camera_name] ) ) array_push(Preview::$cache_map[$camera_name],$medium_cache_name);
            if( !in_array($org_cache_name, Preview::$cache_map[$camera_name] ) ) array_push(Preview::$cache_map[$camera_name],$org_cache_name);
        }

        return array($small_cache_name, $medium_cache_name, $org_cache_name);
    }

    private static function processFile($camera_cache_directory, $original_file, $small_cache_name, $medium_cache_name, $org_cache_name)
    {
        $path_parts = pathinfo($original_file);

        $camera_name = basename($path_parts["dirname"]);

        $org_cache_path = $camera_cache_directory . $org_cache_name;
        $small_cache_path = $camera_cache_directory . $small_cache_name;
        $medium_cache_path = $camera_cache_directory . $medium_cache_name;

        $fp = fopen( $org_cache_path.".lock", "c");
        if( flock($fp, LOCK_EX | LOCK_NB) )
        {
            if( is_file($org_cache_path.".lock") )
            {
                #echo "process " . $org_cache_path ."\n";
                if( !is_file( $org_cache_path ) ) copy($original_file, $org_cache_path);
                if( !is_file( $small_cache_path ) ) Preview::generatePreview($original_file, $small_cache_path, PREVIEW_SMALL_SIZE);
                if( !is_file( $medium_cache_path ) ) Preview::generatePreview($original_file, $medium_cache_path, PREVIEW_MEDIUM_SIZE);

                unlink($org_cache_path.".lock");
            }
            else
            {
                #echo "skipped process " . $org_cache_path ."\n";
            }
            flock($fp, LOCK_UN);
        }
        else
        {
            #echo "skip " . $org_cache_path ."\n";
        }

        fclose($fp);
    }

    //docker exec php sh -c "php -f /dataDisk/htdocs/gallery/preview_generator.php"

    private static function generatePreview($original_file, $preview_file, $preview_size)
    {
        list( $width, $height ) = explode("x", $preview_size);

        $imagick = new Imagick;
        $imagick->readImage( $original_file );
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

        file_put_contents($preview_file, $imagick->getImageBlob());
    }
}
