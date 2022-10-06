RewriteMap lookupUser "txt:/etc/apache2/_.ansible.auth/auth_openidc_users.txt"
RewriteMap lookupGroup "txt:/etc/apache2/_.ansible.auth/auth_openidc_user_groups.txt"
RewriteMap lookupFullname "txt:/etc/apache2/_.ansible.auth/auth_openidc_user_fullnames.txt"

<Location />
    AuthType openid-connect
    ErrorDocument 401 /_auth/unauthorized.html

    RewriteRule ^ - [E=REMOTE_USERNAME:${lookupUser:%{ENV:OIDC_CLAIM_email}},E=REMOTE_USERGROUP:${lookupGroup:%{ENV:OIDC_CLAIM_email}},E=REMOTE_USERFULLNAME:${lookupFullname:%{ENV:OIDC_CLAIM_email}}]
</Location>
