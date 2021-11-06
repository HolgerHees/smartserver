<Location />
    AuthType form
    AuthFormUsername bw_username
    AuthFormPassword bw_password
    AuthFormLocation bw_url
    ErrorDocument 401 /auth/login.html

    AuthName "Authentication required"

    AuthFormProvider file
    AuthUserFile    {{htdocs_path}}secret/.htpasswd

    Session On
    SessionCryptoPassphrase {{vault_form_auth_passphrase}}
    SessionCookieName session_form Path=/;Domain={{server_domain}};Secure;HttpOnly
    #SessionMaxAge 86400
    SessionMaxAge 0

    <RequireAny>
        Require user {{vault_nextcloud_admin_username}}
{% for username in userdata %}{% if 'user' in userdata[username].groups %}
        Require user {{username}}
{% endif %}{% endfor %}
{% if authenticated_ip_addresses is defined and authenticated_ip_addresses | length > 0 %}
        Require ip {{ authenticated_ip_addresses | join(' ') }}
{% endif %}
        Require ip 172.0.0.0/8
        Require local
    </RequireAny>

    RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER}]
</Location>
