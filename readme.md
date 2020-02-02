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

## How to start

To see how you can create your own setup and a lot more, check [the wiki](https://github.com/HolgerHees/smartserver/wiki)
