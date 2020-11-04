<Location />
    AuthName        "{{server_name|capitalize}}"
    AuthType        Basic
    AuthUserFile    {{htdocs_path}}.htpasswd

    <RequireAny>
{% for username in userdata %}
        Require user {{username}}
{% endfor %}
    </RequireAny>

    RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER}]
</Location>
