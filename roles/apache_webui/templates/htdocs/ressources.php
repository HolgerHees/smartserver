<?php
require "./shared/libs/ressources.php";

if( !isset($_GET['type']) ) exit;

Ressources::dump($_GET['type'], __DIR__ . '/main' );
