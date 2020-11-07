<Location />
    AuthName        "{{server_name|capitalize}}"
    AuthType        Basic
    AuthUserFile    {{htdocs_path}}secret/.htpasswd

    <RequireAny>
{% for username in userdata %}{% if 'user' in userdata[username].groups %}
        Require user {{username}}
{% endif %}{% endfor %}
    </RequireAny>

    RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER}]
</Location>
