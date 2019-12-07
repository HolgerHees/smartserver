# Smartserver

This project contains my complete automated IoT Server deployment setup.

[http://www.intranet-of-things.com/smarthome/infrastructure/server/setup/](http://www.intranet-of-things.com/smarthome/infrastructure/server/setup/)

## Requirements

Just install [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/). For an **opensuse** based virtual box container setup, run:

```bash
vagrant --env=demo up suse
```

Or if you want to try a beta version of an **fedora** based demo setup, run:

```bash
vagrant --env=demo up fedora
```

My own deployment setup is reachable via "--env=develop" or "--env=production", but both setups depends on some encrypted vagrant vault files. :-)


You can also use the contained ansible files directly.

```bash
# run everything
ansible-playbook -i server.ini -l demo --ask-vault-pass server.yml

# run everything except vault depending tasks
ansible-playbook -i server.ini -l demo server.yml

# run nextcloud
ansible-playbook -i server.ini -l demo --tags "nextcloud" --ask-vault-pass  server.yml

# run nextcloud without vault depending tasks
ansible-playbook -i server.ini -l demo --tags "nextcloud"  server.yml

```
