<?php
$CONFIG = array (
  'instanceid' => '{{nextcloud_instance_id}}',
  'passwordsalt' => '{{nextcloud_password_salt}}',
  'trusted_domains' => 
  array (
    0 => '{{default_server_ip}}',
    1 => '{{server_domain}}',
    2 => 'nextcloud.{{server_domain}}',
    3 => 'fa-nextcloud.{{server_domain}}',
    4 => 'ba-nextcloud.{{server_domain}}'
  ),
  'preview_max_x' => '2048',
  'preview_max_y' => '2048',
  'allow_local_remote_servers' => true,
  'auth.bruteforce.protection.enabled' => false,
  'overwrite.cli.url' => 'https://nextcloud.{{server_domain}}/',
  'datadirectory' => '{{nextcloud_data_path}}',
  'dbtype' => 'mysql',
  'version' => '{{current_nextcloud_version}}',
  'dbname' => 'nextcloud',
  'dbhost' => 'mariadb',
  'dbtableprefix' => 'oc_',
  'dbuser' => '{{nextcloud_mariadb_username}}',
  'dbpassword' => '{{nextcloud_mariadb_password}}',
  'installed' => true,
  'forcessl' => true,
  'syslog_tag' => 'nextcloud',
  'log_type' => 'file',
  'logfile' => '{{global_log}}nextcloud/nextcloud.log',
  'loglevel' => 2,
  'maintenance' => false,
  'mail_smtpmode' => 'smtp',
  'mail_smtphost' => 'postfix',
  'mail_domain' => '{{server_domain}}',
  'mail_from_address' => 'root',
  'default_phone_region' => '{{country}}',
  'appcodechecker' => false,
  'secret' => '{{nextcloud_secret}}',
  'trashbin_retention_obligation' => 'auto',
  'updatechecker' => false,
  'appstore.experimental.enabled' => true,
  'enabledPreviewProviders' => array (
    'OC\Preview\Movie',
    'OC\Preview\Image',
    'OC\Preview\TXT',
    'OC\Preview\SVG',
    'OC\Preview\Bitmap',
  ),
  'filesystem_check_changes' => 1,
  'filelocking.enabled' => true,
  'memcache.local' => '\\OC\\Memcache\\APCu',
  'memcache.distributed' => '\\OC\\Memcache\\Redis',
  'memcache.locking' => '\\OC\\Memcache\\Redis',
  'redis' => array (
    'host' => 'redis',
    'port' => 6379,
    'timeout' => 0,
    'dbindex' => 0,
  ),
  'mysql.utf8mb4' => true,
  'mail_smtpauthtype' => 'LOGIN',
  'theme' => 'smartserver'
);
