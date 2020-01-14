Alias /auth/relogin/ "{{htdocs_path}}auth/relogin.html"
Alias /auth/ "{{htdocs_path}}auth/"

<Location "/auth/">
    ProxyPass !
    Require all granted
</Location>

<Location "/auth/logout/">
    SetHandler form-logout-handler
    AuthFormLogoutLocation "/auth/relogin/"

    Session on
    SessionCryptoPassphrase {{vault_form_auth_passphrase}}
    SessionCookieName session_form Path=/;Domain={{server_domain}};Secure;HttpOnly
    SessionMaxAge 1
</Location>
