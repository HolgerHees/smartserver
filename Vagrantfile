
Vagrant.configure(2) do |config|
  config.vm.define "develop", autostart: false do |develop|
    develop.vm.box = "generic/opensuse15"
    #develop.vm.box = "opensuse/openSUSE-15.0-x86_64"
    develop.ssh.username = 'vagrant'
    develop.ssh.password = 'vagrant'
    develop.ssh.insert_key = 'true'
    develop.vm.network "private_network", ip: "192.168.1.50"
    #develop.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    #develop.vm.synced_folder "./", "/ansible/smartmarvin/", id: "ansible", :mount_options => ["rw"]
    develop.vm.synced_folder ".", "/vagrant"
    develop.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", "2"]
    end
    
    # Password Input Function
    class Password
        def to_s
        begin
        system 'stty -echo'
        print "Ansible Vault Password: "
        pass = URI.escape(STDIN.gets.chomp)
        ensure
        system 'stty echo'
        end
        print "\n"
        pass
        end
    end

    # Ask for vault password
    develop.vm.provision "shell", env: {"VAULT_PASS" => Password.new}, inline: <<-SHELL
        echo "$VAULT_PASS" > /tmp/vault_pass
    SHELL

    develop.vm.provision "shell", inline: <<-SHELL
      sudo zypper --non-interactive install ansible python-xml
    SHELL

    develop.vm.provision "ansible_local" do |ansible|
      ansible.limit = "develop"
      ansible.playbook = "server.yml"
      ansible.inventory_path = "server.ini"
      ansible.vault_password_file = "/tmp/vault_pass"
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
      #ansible.raw_arguments = "--ask-vault-pass"
      #ansible.ask_vault_pass = true
    end  
    
    # Delete temp vault password file
    develop.vm.provision "shell", inline: <<-SHELL
        rm /tmp/vault_pass
    SHELL
  end

  config.vm.define "develop_fedora", autostart: false do |develop_fedora|
    develop_fedora.vm.box = "fedora/31-cloud-base"
    develop_fedora.ssh.username = 'vagrant'
    develop_fedora.ssh.password = 'vagrant'
    develop_fedora.ssh.insert_key = 'true'
    develop_fedora.vm.network "private_network", ip: "192.168.1.50"
    #develop_fedora.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    #develop_fedora.vm.synced_folder "./", "/ansible/smartmarvin/", id: "ansible", :mount_options => ["rw"]
    develop_fedora.vm.synced_folder ".", "/vagrant"
    develop_fedora.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", "2"]
    end

    # Password Input Function
    class Password
        #require 'socket'
        #require 'timeout'
        #require 'net/ssh'
        
        def to_s
            
            #print "test ssh"
            #begin
            #    session = Net::SSH.start( '192.168.1.50', 'vagrant', password: "vagrant" )
            #    session.close
            #    #Socket.tcp("192.168.1.50", 22, connect_timeout: 60) {}
            #    print "... ok\n"
            #rescue Errno::ECONNREFUSED, Errno::EHOSTUNREACH
                
            #    print "... reboot\n"
            #    system("vagrant reload") 
            #end

            #is_port_open?("192.168.1.50", 22, 60, 1) {}
            
            #print "done\n"
            
            begin
                system 'stty -echo'
                print "Ansible Vault Password: "
                pass = URI.escape(STDIN.gets.chomp)
            ensure
                system 'stty echo'
            end
            print "\n"
            pass
        end
    end

    #$script = <<-SHELL
    #    if ! grep -q "unified_cgroup_hierarchy" /etc/default/grub; then
    #        echo "change cgroup config for docker"
    #        sed -e 's/\\(GRUB_CMDLINE_LINUX="[^"]*\\)\\(".*\\)/\\1 systemd.unified_cgroup_hierarchy=0\\2/' /etc/default/grub > /etc/default/grub
    #        cat /etc/default/grub
            
    #        grub2-mkconfig -o /boot/grub2/grub.cfg
            
    #        echo "reboot to activate cgroup changes"

    #        sync
            
    #        echo "1"

    #        systemctl stop sshd
            
    #        echo "2"
            
    #        exit
    #    fi
    #SHELL
    
    #develop_fedora.vm.provision "shell", inline: $script

    # Ask for vault password
    develop_fedora.vm.provision "shell", env: {"VAULT_PASS" => Password.new}, inline: <<-SHELL
        echo "$VAULT_PASS" > /tmp/vault_pass
    SHELL

    develop_fedora.vm.provision "shell", inline: <<-SHELL
      sudo yum --assumeyes install ansible python
    SHELL

    develop_fedora.vm.provision "ansible_local" do |ansible|
      ansible.limit = "develop"
      ansible.playbook = "server.yml"
      ansible.inventory_path = "server.ini"
      ansible.vault_password_file = "/tmp/vault_pass"
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
      ansible.become = true
      ansible.become_user = "root"
      #ansible.raw_arguments = "--ask-vault-pass"
      #ansible.ask_vault_pass = true
    end  
    
    # Delete temp vault password file
    develop_fedora.vm.provision "shell", inline: <<-SHELL
        rm /tmp/vault_pass
    SHELL
  end
end
