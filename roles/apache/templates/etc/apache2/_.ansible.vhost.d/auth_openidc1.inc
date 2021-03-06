RewriteMap lookup "txt:/etc/apache2/_.ansible.vhost.d/auth_openidc_users.txt"

<Location />
    AuthType openid-connect
    ErrorDocument 401 /auth/unauthorized.html

    <RequireAny>
{% for username in userdata %}{% if 'user' in userdata[username].groups %}
        Require claim email:{{userdata[username].email}}
{% endif %}{% endfor %}
        Require ip {{ authenticated_ip_addresses | join(' ') }}
        Require ip 172.0.0.0/8
        Require local
    </RequireAny>

    RewriteRule ^ - [E=REMOTE_USERNAME:${lookup:%{ENV:OIDC_CLAIM_email}}]
</Location>
