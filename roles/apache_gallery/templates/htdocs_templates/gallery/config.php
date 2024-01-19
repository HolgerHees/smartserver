<?php
date_default_timezone_set("{{timezone}}");

define( "FTP_FOLDER", "{{ftp_path}}");
define( "MAX_PREVIEW_AGE", "{{ftp_max_file_age}}");
define( "CACHE_DIRECTORY", __DIR__ . "/cache/" );

define( "PREVIEW_SMALL_SIZE", "600x400");
define( "PREVIEW_MEDIUM_SIZE", "900x500"); //"450x250";
