<Location />
    AuthType form
    AuthFormUsername bw_username
    AuthFormPassword bw_password
    ErrorDocument 401 /auth/login.html

    AuthName "Authentication required"

    AuthFormProvider file
    AuthUserFile    {{htdocs_path}}.htpasswd
    AuthGroupFile   {{htdocs_path}}.htgroups

    Session On
    SessionCryptoPassphrase {{vault_form_auth_passphrase}}
    SessionCookieName session_form Path=/;Domain={{server_domain}};Secure;HttpOnly
    #SessionMaxAge 86400
    SessionMaxAge 0

    <RequireAny>
        Require group user
        Require ip {{ authenticated_ip_addresses | join(' ') }}
        Require ip 172.0.0.0/8
        Require local
    </RequireAny>

    RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER}]
</Location>
