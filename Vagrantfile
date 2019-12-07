require 'getoptlong'

opts = GetoptLong.new(
    [ '--env', GetoptLong::OPTIONAL_ARGUMENT ]
)

limit='demo'

begin
  opts.each do |opt, arg|
    case opt
      when '--env'
        if arg == "demo" then
            limit = "demo"
        else
            limit = "develop"
        end
    end
  end
  rescue
end

Vagrant.configure(2) do |config|
  config.vm.define "suse", autostart: false do |develop_suse|
    develop_suse.vm.box = "generic/opensuse15"
    #develop_suse.vm.box = "opensuse/openSUSE-15.0-x86_64"
    develop_suse.ssh.username = 'vagrant'
    develop_suse.ssh.password = 'vagrant'
    develop_suse.ssh.insert_key = 'true'
    develop_suse.vm.network "private_network", ip: "192.168.1.50"
    #develop_suse.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    #develop_suse.vm.synced_folder "./", "/ansible/smartmarvin/", id: "ansible", :mount_options => ["rw"]
    develop_suse.vm.synced_folder ".", "/vagrant"
    develop_suse.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", "2"]
    end
    
    # Ask for vault password
    develop_suse.vm.provision "shell", env: {"VAULT_PASS" => limit == 'demo' ? "" : Password.new}, inline: <<-SHELL
        echo "$VAULT_PASS" > /tmp/vault_pass
    SHELL

    develop_suse.vm.provision "shell", inline: <<-SHELL
      sudo zypper --non-interactive install ansible python-xml
    SHELL
    
    develop_suse.vm.provision "ansible_local" do |ansible|
      ansible.limit = limit
      ansible.playbook = "server.yml"
      ansible.inventory_path = "server.ini"
      if limit != 'demo' then
        ansible.vault_password_file = "/tmp/vault_pass"
      end
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
      #ansible.raw_arguments = "--ask-vault-pass"
      #ansible.ask_vault_pass = true
    end  
    
    # Delete temp vault password file
    develop_suse.vm.provision "shell", inline: <<-SHELL
        rm /tmp/vault_pass
    SHELL
  end

  config.vm.define "fedora", autostart: false do |develop_fedora|
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

    develop_fedora.vm.provision "shell", inline: <<-SHELL
      sudo yum --assumeyes install ansible python
    SHELL

    develop_fedora.vm.provision "ansible_local" do |ansible|
      ansible.limit = limit
      ansible.playbook = "roles/container/tasks/fedora.yml"
      ansible.inventory_path = "server.ini"
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
      ansible.become = true
      ansible.become_user = "root"
      #ansible.raw_arguments = "--ask-vault-pass"
      #ansible.ask_vault_pass = true
    end  

    # Ask for vault password
    develop_fedora.vm.provision "shell", env: {"VAULT_PASS" => limit == 'demo' ? "" : Password.new}, inline: <<-SHELL
        echo "$VAULT_PASS" > /tmp/vault_pass
    SHELL

    develop_fedora.vm.provision "ansible_local" do |ansible|
      ansible.limit = "develop"
      ansible.playbook = "server.yml"
      ansible.inventory_path = "server.ini"
      if limit != 'demo' then
        ansible.vault_password_file = "/tmp/vault_pass"
      end
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

# Password Input Function
class Password
    require 'socket'
    require 'timeout'
    require 'net/ssh'
    
    def to_s
        print "check server reachability "
        begin
            #session = Net::SSH.start( '192.168.1.50', 'vagrant', password: "vagrant" )
            #session.close
            Socket.tcp("192.168.1.50", 22, connect_timeout: 1) {}
            print " ok\n"
        rescue Exception => e #Errno::ECONNREFUSED, Errno::EHOSTUNREACH
            print "." # + e.message
            retry
        end
        
        pass = nil
        loop do
          begin
              system 'stty -echo'
              print "Ansible Vault Password: "
              pass = URI.escape(STDIN.gets.chomp)
          ensure
              system 'stty echo'
          end
          print "\n"
          
          if not pass.empty?
            break
          end
        end

        pass
    end
end
