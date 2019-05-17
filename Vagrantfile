
Vagrant.configure(2) do |config|
  config.vm.define "test" do |test|
    test.vm.box = "opensuse/openSUSE-15.0-x86_64"
    #test.vm.box = "opensuse/openSUSE-Tumbleweed-x86_64"
    test.ssh.username = 'root'
    test.ssh.password = 'vagrant'
    test.ssh.insert_key = 'true'
    test.vm.network "private_network", ip: "192.168.1.50"
    #test.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    #test.vm.synced_folder "./", "/ansible/smartmarvin/", id: "ansible", :mount_options => ["rw"]
    test.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", "2"]
    end
    
    test.vm.provision "shell", inline: <<-SHELL
      sudo zypper --non-interactive install ansible
    SHELL

    test.vm.provision "ansible_local" do |ansible|
      ansible.limit = "test"
      ansible.playbook = "server.yml"
      ansible.inventory_path = "server.ini"
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
    end  
  end
  
  config.vm.define "develop", autostart: false do |develop|
    develop.vm.box = "opensuse/openSUSE-15.0-x86_64"
    #develop.vm.box = "opensuse/openSUSE-Tumbleweed-x86_64"
    develop.ssh.username = 'root'
    develop.ssh.password = 'vagrant'
    develop.ssh.insert_key = 'true'
    develop.vm.network "private_network", ip: "192.168.1.50"
    #develop.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    #develop.vm.synced_folder "./", "/ansible/smartmarvin/", id: "ansible", :mount_options => ["rw"]
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
      sudo zypper --non-interactive install ansible
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
    develop_fedora.vm.box = "fedora/30-cloud-base"
    develop_fedora.ssh.username = 'vagrant'
    develop_fedora.ssh.password = 'vagrant'
    develop_fedora.ssh.insert_key = 'true'
    develop_fedora.vm.network "private_network", ip: "192.168.1.50"
    #develop_fedora.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    #develop_fedora.vm.synced_folder "./", "/ansible/smartmarvin/", id: "ansible", :mount_options => ["rw"]
    develop_fedora.vm.provider :virtualbox do |vb|
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
