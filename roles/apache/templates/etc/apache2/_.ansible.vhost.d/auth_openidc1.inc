RewriteMap lookup "txt:/etc/apache2/_.ansible.vhost.d/auth_openidc_users.txt"

<Location />
    AuthType openid-connect
    ErrorDocument 401 /auth/unauthorized.html

    <RequireAny>
{% for username in vault_usernames %}
        Require claim email:{{vault_userdata[username].email}}
{% endfor %}
        Require ip {{ authenticated_ip_addresses | join(' ') }}
        Require local
    </RequireAny>

    RewriteRule ^ - [E=REMOTE_USERNAME:${lookup:%{ENV:OIDC_CLAIM_email}}]
</Location>
