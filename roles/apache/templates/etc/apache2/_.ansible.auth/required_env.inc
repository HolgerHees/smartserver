{% if vault_openid_connect_url != 'None' %}
RewriteCond %{ENV:OIDC_CLAIM_email} !^$
RewriteRule ^ - [E=REMOTE_USERNAME:${lookupUser:%{ENV:OIDC_CLAIM_email}},E=REMOTE_USERGROUP:${lookupGroup:%{ENV:OIDC_CLAIM_email}},E=REMOTE_USERFULLNAME:${lookupFullname:%{ENV:OIDC_CLAIM_email}},NS]
{% endif %}

RewriteCond %{REMOTE_USER} !^$
{% if vault_openid_connect_url != 'None' %}
RewriteCond %{ENV:OIDC_CLAIM_email} ^$
{% endif %}
RewriteRule ^ - [E=REMOTE_USERNAME:%{REMOTE_USER},E=REMOTE_USERGROUP:${lookupGroup:%{REMOTE_USER}},E=REMOTE_USERFULLNAME:${lookupFullname:%{REMOTE_USER}},NS]

RequestHeader set X-Forwarded-User %{REMOTE_USERNAME}e env=REMOTE_USERNAME
RequestHeader unset X-Forwarded-User env=!REMOTE_USERNAME

RequestHeader set X-Forwarded-UserGroup %{REMOTE_USERGROUP}e env=REMOTE_USERGROUP
RequestHeader unset X-Forwarded-UserGroup env=!REMOTE_USERGROUP

RequestHeader set X-Forwarded-UserFullname %{REMOTE_USERFULLNAME}e env=REMOTE_USERFULLNAME
RequestHeader unset X-Forwarded-UserFullname env=!REMOTE_USERFULLNAME

