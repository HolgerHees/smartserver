RewriteMap lookupGroup "txt:/etc/apache2/_.ansible.auth/auth_user_groups.txt"
RewriteMap lookupFullname "txt:/etc/apache2/_.ansible.auth/auth_user_fullnames.txt"

<Location />
    AuthType form
    AuthFormUsername bw_username
    AuthFormPassword bw_password
    AuthFormLocation bw_url
    ErrorDocument 401 /auth/login.html

    AuthName "Authentication required"

    AuthFormProvider file
    AuthUserFile    /etc/apache2/_.ansible.auth/.htpasswd

    Session On
    SessionCryptoPassphrase {{vault_form_auth_passphrase}}
    SessionCookieName session_form Path=/;Domain={{server_domain}};Secure;HttpOnly
    #SessionMaxAge 86400
    SessionMaxAge 0

    RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER},E=REMOTE_USERGROUP:${lookupGroup:%{REMOTE_USER}},E=REMOTE_USERFULLNAME:${lookupFullname:%{REMOTE_USER}}]
</Location>
