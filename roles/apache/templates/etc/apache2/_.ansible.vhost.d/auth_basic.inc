RewriteMap lookupGroup "txt:/etc/apache2/_.ansible.auth/auth_user_groups.txt"
RewriteMap lookupFullname "txt:/etc/apache2/_.ansible.auth/auth_user_fullnames.txt"

<Location />
    AuthName        "{{server_name|capitalize}}"
    AuthType        Basic
    AuthUserFile    /etc/apache2/_.ansible.auth/.htpasswd

    <RequireAny>
{% for username in userdata %}{% if 'user' in userdata[username].groups %}
        Require user {{username}}
{% endif %}{% endfor %}
    </RequireAny>

    RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER},E=REMOTE_USERGROUP:${lookupGroup:%{REMOTE_USER}},E=REMOTE_USERFULLNAME:${lookupFullname:%{REMOTE_USER}}]
</Location>
