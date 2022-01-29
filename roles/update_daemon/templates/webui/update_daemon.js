{% if update_daemon_software_check_enabled %}mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_software', '/update_software/', 'admin', 310, '{i18n_Software}', '{i18n_Software status}', false, "update_software_logo.svg");
{% endif %}
{% if update_daemon_system_check_enabled %}mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_system', '/update_system/', 'admin', 311, '{i18n_Updates}', '{i18n_System updates}', false, "update_system_logo.svg");
{% endif %}
