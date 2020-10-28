# -*- coding: utf-8 -*-
LOG_PREFIX = "jsr223.jython"

admin_email = "admin_email@some_domain.com"

openhabHost = "localhost"
openhabPort = "8080"# "8443"

allTelegramBots = [
{% for bot_name in vault_telegram_bots %}
  {% if loop.index > 1 %},{% endif %}"{{bot_name}}"
{% endfor %}
]
