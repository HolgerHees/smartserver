Alias /_auth/relogin/ "{{htdocs_path}}_auth/relogin.html"
Alias /_auth/ "{{htdocs_path}}_auth/"

<Location "/_auth/">
    ProxyPass !
    Require all granted
</Location>

<Location "/_auth/logout/">
    SetHandler form-logout-handler
    AuthFormLogoutLocation "/_auth/relogin/"

    Session on
    SessionCryptoPassphrase {{vault_form_auth_passphrase}}
    SessionCookieName session_form Path=/;Domain={{server_domain}};Secure;HttpOnly
    SessionMaxAge 1
</Location>
