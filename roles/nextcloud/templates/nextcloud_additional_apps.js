var subGroup = mx.Menu.getMainGroup('workspace').getSubGroup('nextcloud');
{% for entry in nextcloud_additional_apps %}
subGroup.addUrl('{{entry.app}}','//nextcloud.{host}/index.php/apps/{{entry.app}}/', ['{{ '\',\''.join(entry.usergroups) | default('user')}}'], {{entry.order | default(200)}}, '{{entry.name}}', {{'\'' + entry.description + '\'' | default('null')}}, false, {{'\'' + ( entry.icon | basename ) + '\'' | default('null')}});
{% endfor %}
