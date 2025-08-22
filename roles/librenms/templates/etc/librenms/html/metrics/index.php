<?php
require __DIR__ . '/../../LibreNMS/Data/Store/Prometheus.php';

header("Content-Type: text/plain; charset=UTF-8");

$prometheus = new LibreNMS\Data\Store\Prometheus();
$prometheus->processMetrics();

