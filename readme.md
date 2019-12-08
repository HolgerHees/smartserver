# Smartserver

This project contains my complete automated IoT Server deployment setup.

[http://www.intranet-of-things.com/smarthome/infrastructure/server/setup/](http://www.intranet-of-things.com/smarthome/infrastructure/server/setup/)

## Requirements

Just install [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/). For an **opensuse** based virtual box container setup, run:

```bash
vagrant --config=demo --os=suse up
```

Or if you want to try a beta version of an **fedora** based demo setup, run:

```bash
vagrant --config=demo --os=fedora up
```

You can also use the contained ansible files directly.

```bash
# run everything
ansible-playbook -i config/demo/server.ini --ask-vault-pass server.yml

# run everything except vault depending tasks
ansible-playbook -i config/demo/server.ini server.yml

# run nextcloud
ansible-playbook -i config/demo/server.ini --tags "nextcloud" --ask-vault-pass server.yml

# run nextcloud without vault depending tasks
ansible-playbook -i config/demo/server.ini --tags "nextcloud" server.yml

```
