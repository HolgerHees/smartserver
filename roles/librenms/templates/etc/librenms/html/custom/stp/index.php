<?php
use LibreNMS\Util\Laravel;

$rootPath = __DIR__ . "/../../../";

chdir($rootPath);

require_once $rootPath . 'vendor/autoload.php';

use LibreNMS\DB\Eloquent;

$init_modules = [];#'alerts', 'laravel', 'nodb'];
require $rootPath . 'includes/init.php';

$stps = Eloquent::DB()->select("SELECT `device_id`, `designatedRoot` FROM `ports_stp` GROUP BY `device_id`", (array) []);

$result = [
    "status" => "ok",
    "stp" => []
];
foreach ($stps as $stp) {
    if( empty($stp->designatedRoot) )
    {
        continue;
    }

    $result['stp'][] = [
        'device_id' => $stp->device_id,
        'uplink_mac' => rtrim(chunk_split($stp->designatedRoot, 2, ":"), ":")
    ];
}

header('Content-Type: application/json; charset=utf-8');
echo json_encode($result);
