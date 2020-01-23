# Smartserver

This project contains my complete automated IoT Server deployment setup.

For a detailed overview about installed software and services check

* [http://www.intranet-of-things.com/smarthome/infrastructure/server/setup/](http://www.intranet-of-things.com/smarthome/infrastructure/server/setup/) 
* or the main deployment [server.yml](https://github.com/HolgerHees/smartserver/blob/master/server.yml) file

For a detailed description about the main features and a lot more, check [the wiki](https://github.com/HolgerHees/smartserver/wiki)

## Demo setup

Install [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/). The virtual machine needs at least 6GB of memory. On production I run it on a [4 core atom processor with 32GB memory](http://www.intranet-of-things.com/smarthome/infrastructure/server/), but 16GB should be fine too.

For an [opensuse](https://www.opensuse.org/) based demo setup, run:

```bash
vagrant --config=demo --os=suse up
```

Or if you want to try a beta version of an [fedora](https://getfedora.org/) based demo setup, run:

```bash
vagrant --config=demo --os=fedora up
```

If the deployment is done, add the folowing entries to your host file.

```bash
192.168.1.50    smartserver.test
192.168.1.50    nextcloud.smartserver.test
192.168.1.50    kibana.smartserver.test
192.168.1.50    openhab.smartserver.test
192.168.1.50    netdata.smartserver.test
192.168.1.50    grafana.smartserver.test
192.168.1.50    ba.smartserver.test
```

As everything is ready, open https://smartserver.test/ in your webbrower and login with username "testuser" and password "test".

Maybe you have to accept the certificate for all individual subdomains separately, because they are selfsigned in the demo setup.

## Create your own deployment

Copy `./config/demo/` to `./config/myserver` and modify all included files to your needs. 

* In the `server.ini` file, you should modify only the hostname from `demo` to `myserver`

* In the `env.yml` file you can specify the dns name, and main ip's for production and development setup. This allows the deployment skript to detect automatically if it is running on production or not.

* The `vault` folder contains all files which are encrypted by using the cmd `./vault.sh`

  * The `vault/vault.yml` contains mainly usernames, passwords and secret id's

  * Later, the `vault` folder will contain also certificates.
  
Now, run:

```bash
vagrant --config=myserver --os=suse up
```
  
## Add apache and openssl certificates to your deployment config

After the first deployment, initial apache and openssl certificates are created. 

To make them part of your deployment config, copy all files to your 'vault' folder by running the following commands on your deployed server.

```bash
# copied all certificate files to
# - 'config/myserver/vault_backup/easy-rsa/'
# - 'config/myserver/vault_backup/letsencrypt/'
# - 'config/myserver/vault_backup/openvpn/'
ansible-playbook -i config/myserver/server.ini utils/backup_certificates.yml

# copied all files to your vault folder.
mv config/myserver/vault_backup/* config/myserver/vault/
rmdir config/myserver/vault_backup/

# encrypts all new vault files
./vault.sh encrypt
```

## Usage of './vault.sh'

The command `./vault.sh` is used to encrypt and decrypt the whole `./config/*/vault` recursively. It simplifies the encryption and decryption procedure by handling all files at once.

To encrypt everything run:

```bash
./vault.sh encrypt
```

and to decrypt everything run:

```bash
./vault.sh decrypt
```

The command checks if a file is already encrypted/decrypted and is encrypting/decrypting it only if needed.

## Use ansible directly

You can also use the contained ansible files directly.

```bash
# deploys everything
ansible-playbook -i config/demo/server.ini --ask-vault-pass server.yml

# deploys everything except vault depending tasks
ansible-playbook -i config/demo/server.ini server.yml

# deploy only nextcloud
ansible-playbook -i config/demo/server.ini --tags "nextcloud" --ask-vault-pass server.yml

# deploy only nextcloud without vault depending tasks
ansible-playbook -i config/demo/server.ini --tags "nextcloud" server.yml
```

## Continuous integration testing

coming soon
