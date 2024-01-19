<?php

class Preview {
    static $cache_map = array();

    public static function check($original_file, $process)
    {
        $path_parts = pathinfo($original_file);
        $camera_name = basename($path_parts["dirname"]);
        $camera_cache_directory = CACHE_DIRECTORY . $camera_name . "/";

        if( !array_key_exists($camera_name, Preview::$cache_map) )
        {
            if( !is_dir( $camera_cache_directory ) ) mkdir( $camera_cache_directory, 0750, true );

            Preview::$cache_map[$camera_name] = array_fill_keys( scandir($camera_cache_directory), 1 );
        }

        $small_cache_name = $path_parts["filename"] . "_small.jpg";
        $medium_cache_name = $path_parts["filename"] . "_medium.jpg";
        $org_cache_name = $path_parts["basename"];

        if( !isset(Preview::$cache_map[$camera_name][$small_cache_name]) || !isset(Preview::$cache_map[$camera_name][$medium_cache_name]) || !isset(Preview::$cache_map[$camera_name][$org_cache_name]) )
        {
            if( $process )
            {
                Preview::processFile($camera_cache_directory, $original_file, $small_cache_name, $medium_cache_name, $org_cache_name);
            }
            else
            {
                return array(null, null, null);
            }
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
                //echo "process " . $org_cache_path ."\n";
                if( !is_file( $org_cache_path ) ) copy($original_file, $org_cache_path);
                $img = null;
                if( !is_file( $medium_cache_path ) ) $img = Preview::generatePreview($img, $original_file, $medium_cache_path, PREVIEW_MEDIUM_SIZE);
                if( !is_file( $small_cache_path ) ) $img = Preview::generatePreview($img, $original_file, $small_cache_path, PREVIEW_SMALL_SIZE);

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

    private static function generatePreview($img, $original_file, $preview_file, $preview_size)
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
    }
}
