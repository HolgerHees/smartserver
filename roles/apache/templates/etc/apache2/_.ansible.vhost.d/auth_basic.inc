<Location />
    AuthName        "{{server_name|capitalize}}"
    AuthType        Basic
    AuthUserFile    {{htdocs_path}}.htpasswd
    AuthGroupFile   {{htdocs_path}}.htgroups

    Require group user

    RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER}]
</Location>
