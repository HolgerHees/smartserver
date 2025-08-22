<?php
namespace LibreNMS\Data\Store;

use App\Polling\Measure\Measurement;
use LibreNMS\Config;
use LibreNMS\Util\Proxy;
use Log;

use LibreNMS\DB\Eloquent;

if( !class_exists("LibreNMS\Data\Store\BaseDatastore") )
{
    # metrics endpoint
    $init_modules = [];#'alerts', 'laravel', 'nodb'];
    require __DIR__ . '/../../../includes/init.php';
    //Log::setDefaultDriver('console');
}
else
{
    # internal codepath
    $result = Eloquent::DB()->select("SHOW TABLES LIKE 'custom_metrics'", (array) []);
    if( count($result) == 0 )
    {
        $sql = "CREATE TABLE `custom_metrics` (
                  `device_id` int(10) UNSIGNED NOT NULL,
                  `messurement` varchar(255) NOT NULL,
                  `labels` varchar(255) NOT NULL,
                  `value` varchar(255) NOT NULL,
                  `datetime` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci";
        $result = Eloquent::DB()->select($sql, (array) []);

        $sql = "ALTER TABLE `custom_metrics` ADD PRIMARY KEY (`device_id`,`messurement`,`labels`)";
        $result = Eloquent::DB()->select($sql, (array) []);
    }
}

class Prometheus extends BaseDatastore
{
    private $job;
    private $prune_threshold_seconds;

    public function __construct()
    {
        parent::__construct();

        // shared config
        $this->job = "librenms";

        // local config
        $this->prune_threshold_seconds = 900;


        $this->device_group_devices = [];
    }

    public function getName(): string
    {
        return 'Prometheus';
    }

    public static function isEnabled(): bool
    {
        return true;
    }

    public function write(string $measurement, array $fields, array $tags = [], array $meta = []): void
    {
        $device = $this->getDevice($meta);

        $rows = [];
        foreach( $fields as $_name => $_value )
        {
            [$_measurement, $labels, $value] = $this->processMeasurement($measurement, $_name, $_value, $tags);
            if( $value === null ) continue;

            $rows[] = [
                    'device_id' => $device->device_id,
                    'messurement' => $_measurement,
                    'labels' => $labels,
                    'value' => $value
            ];
        }
        Eloquent::DB()->table('custom_metrics')->upsert($rows, [ 'device_id', 'messurement', 'labels' ], [ 'value' ] );
    }

    public function processMetrics()
    {
        global $PDO_FETCH_ASSOC;
        $PDO_FETCH_ASSOC = true;

        $time = floor(microtime(true) * 1000);

        $device_ports = [];
        $_ports = Eloquent::DB()->cursor("SELECT `device_id`, `ifIndex`, `ifAlias`, `ifName`, `ifOperStatus`, `ifSpeed`, `ignore` FROM `ports`", (array) []);
        foreach ($_ports as $port) {
            if (!isset($device_ports[ $port->device_id])) $device_ports[$port->device_id] = [];
            $device_ports[$port->device_id][$port->ifIndex] = $port;
        }

        $device_group_names = [];
        $_device_groups = Eloquent::DB()->cursor("SELECT `id`,`name` FROM `device_groups`", (array) []);
        foreach ($_device_groups as $device_group) {
            $device_group_names[ $device_group->id ] = $device_group->name;
        }

        $device_group_devices = [];
        $_device_group_devices = Eloquent::DB()->cursor("SELECT `device_group_id`,`device_id` FROM `device_group_device`", (array) []);
        foreach ($_device_group_devices as $device_group_device) {
            if (!isset($device_group_devices[ $device_group_device->device_id ])) {
                $device_group_devices[ $device_group_device->device_id ] = [];
            }
            $device_group_devices[ $device_group_device->device_id ][] = $device_group_device->device_group_id;
        }

        $devices = [];
        $_devices = Eloquent::DB()->cursor("SELECT `device_id`, `ignore`, `hostname`, `sysName`, `status` FROM `devices`", (array) []);//(array) $parameters);
        foreach ($_devices as $device) {
            $alertingEnabled = $device->ignore ? 0 : 1;

            $devices[$device->device_id] = $device;

            $data_r = [];
            foreach( $device_ports[$device->device_id] as $device_port_ifIndex => $port )
            {
                $_tags = [];
                $_tags['ifIndex'] = $port->ifIndex;
                $_tags['ifAlias'] = $port->ifAlias;
                $_tags['ifName'] = $port->ifName;

                $_tags_r = $this->applyGroups( $device_group_devices, $device_group_names, $device, $_tags );

                $measurements = [];
                $measurements['ifOperational'] = $port->ifOperStatus == 'down' ? 0 : 1;
                $measurements['ifSpeed'] = $port->ifSpeed;
                $measurements['alerting'] = !$alertingEnabled || $port->ignore ? 0 : 1;

                foreach( $_tags_r as $_tags )
                {
                    foreach( $measurements as $_name => $_value )
                    {
                        [$messurement, $labels, $value] = $this->processMeasurement('ports', $_name, $_value, $_tags);
                        if( $value === null ) continue;

                        $this->printMeasurement($time, $device, $messurement, $labels, $value);
                    }
                }
            }

            $_tags = [];
            $_tags_r = $this->applyGroups( $device_group_devices, $device_group_names, $device, $_tags );

            $measurements = [];
            $measurements['alerting'] = $alertingEnabled;
            $measurements['state'] = $device->status ? 1 : 0;

            foreach( $_tags_r as $_tags )
            {
                foreach( $measurements as $_name => $_value )
                {
                    [$messurement, $labels, $value] = $this->processMeasurement('device', $_name, $_value, $_tags);
                    if( $value === null ) continue;

                    $this->printMeasurement($time, $device, $messurement, $labels, $value);
                }
            }
        }

        $_metrics = Eloquent::DB()->cursor("SELECT * FROM `custom_metrics`", (array) []);
        foreach ($_metrics as $metric) {
            $this->printMeasurement($time, $devices[$metric->device_id], $metric->messurement, $metric->labels, $metric->value);
        }

        Eloquent::DB()->select("DELETE FROM `custom_metrics` WHERE `datetime` < DATE_SUB(NOW() , INTERVAL " . $this->prune_threshold_seconds . " SECOND)", (array) []);
    }

    private function applyGroups($device_group_devices, $device_group_names, $device, $tags)
    {
        if (isset($device_group_devices[$device->device_id] ))
        {
            $group_ids = $device_group_devices[$device->device_id];
            if (count($group_ids) > 0 )
            {
                $tags_r = [];
                foreach( $group_ids as $group_id )
                {
                    $tags['group'] = $device_group_names[$group_id];
                    $tags_r[] = $tags;
                }
                return $tags_r;
            }
        }

        return [ $tags ];
    }

    private function printMeasurement($time, $device, $messurement, $labels, $value) {
        $pre_labels = array();
        array_push($pre_labels, "job=\"" . $this->job . "\"");
        array_push($pre_labels, "instance=\"" . $device->hostname . "\"");
        array_push($pre_labels, "sysname=\"".$device->sysName."\"");

        echo 'librenms_' . $messurement . "{" . implode(',',$pre_labels) . ( $labels ? "," . $labels : "" ) . "} " . $value . " $time\n";
    }

    private function processMeasurement($measurement, $name, $value, $tags )
    {
        if( $value === null || !is_numeric($value) ) return [null, null, null];

        $labels = array();
        array_push($labels, "measurement=\"" . addcslashes($measurement,'\\') . "\"");

        $preprocessed_tags = [];
        foreach ($tags as $tag_name => $tag_value) {
            if (strpos($tag_name, 'rrd_') === 0) {
                if( $name != "toner" ) continue;
                //if ( in_array($tag_name, ["rrd_def"]) ) continue;

                if( $tag_name == "rrd_name" ) {
                    $tag_name = "supply_type";
                    $tag_value = $tag_value[1];
                }
                else if( $tag_name == "rrd_oldname" ) {
                    $tag_name = "supply_descr";
                    $tag_value = $tag_value[1];
                }
                else
                {
                    continue;
                }
            }

            $preprocessed_tags[$tag_name] = $tag_value;
        }

        foreach ($preprocessed_tags as $tag_name => $tag_value) {
            if ($tag_value === null) continue;
            array_push($labels, "$tag_name=\"" . addcslashes($tag_value,'\\') . "\"");
        }

        $measurement = str_replace("-", "_", $measurement);
        $key = str_replace("-", "_", $name);
        if( $measurement != $key && !str_ends_with( $measurement, "_" . $key ) ) $measurement .= "_" . $key;

        $labels = implode(',',$labels);

        return [$measurement, $labels, $value];
    }

    /**
     * Checks if the datastore wants rrdtags to be sent when issuing put()
     *
     * @return bool
     */
    public function wantsRrdTags()
    {
        return true;
    }
}
