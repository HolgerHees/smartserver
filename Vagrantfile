require 'getoptlong'

opts = GetoptLong.new(
    ['--env', GetoptLong::OPTIONAL_ARGUMENT], ['--os', GetoptLong::OPTIONAL_ARGUMENT ]
)

os="suse"
image="generic/opensuse15"
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
      when '--os'
        if arg == "suse" then
            os = "suse"
            image = "generic/opensuse15"
        else
            os = "fedora"
            image = "fedora/31-cloud-base"
        end
    end
  end
  rescue
end

Vagrant.configure(2) do |config|
  config.vm.define "suse", autostart: true do |setup|
    setup.vm.box = image
    setup.ssh.username = 'vagrant'
    setup.ssh.password = 'vagrant'
    setup.ssh.insert_key = 'true'
    setup.vm.network "private_network", ip: "192.168.1.50"
    #setup.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    #setup.vm.synced_folder "./", "/ansible/smartmarvin/", id: "ansible", :mount_options => ["rw"]
    setup.vm.synced_folder ".", "/vagrant"
    setup.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", "2"]
    end
    
    if os == 'fedora' then
        setup.vm.provision "ansible_local" do |ansible|
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
    end  

    # Ask for vault password
    setup.vm.provision "shell", env: {"VAULT_PASS" => limit == 'demo' ? "" : Password.new}, inline: <<-SHELL
        echo "$VAULT_PASS" > /tmp/vault_pass
    SHELL

    if os == 'suse' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo zypper --non-interactive install ansible python-xml
        SHELL
    else
        setup.vm.provision "shell", inline: <<-SHELL
        sudo yum --assumeyes install ansible python
        SHELL
    end
    
    setup.vm.provision "ansible_local" do |ansible|
      ansible.limit = limit
      ansible.playbook = "server.yml"
      ansible.inventory_path = "server.ini"
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
      
      if limit != 'demo' then
        ansible.vault_password_file = "/tmp/vault_pass"
      end

      if os == 'fedora' then
        ansible.become = true
        ansible.become_user = "root"
      end
    end  
    
    # Delete temp vault password file
    setup.vm.provision "shell", inline: <<-SHELL
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
