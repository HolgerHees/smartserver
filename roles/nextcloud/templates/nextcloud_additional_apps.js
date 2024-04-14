var subGroup = mx.Menu.getMainGroup('workspace').getSubGroup('nextcloud');
{% for entry in nextcloud_additional_apps %}
subGroup.addUrl('{{entry.app}}', ['{{ '\',\''.join(entry.usergroups) | default('user')}}'], '//nextcloud.{host}/index.php/apps/{{entry.app}}/', { 'order': {{entry.order | default(200)}}, 'title': '{{entry.name}}', 'info': {{'\'' + entry.description + '\'' | default('null')}}, 'icon': {{'\'' + ( entry.icon | basename ) + '\'' | default('null')}}, 'callbacks': { 'ping': mx.Nextcloud.applyTheme } });
{% endfor %}
