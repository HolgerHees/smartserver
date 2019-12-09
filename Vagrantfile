require 'getoptlong'

opts = GetoptLong.new(
    [ '--help', '-h', GetoptLong::NO_ARGUMENT ],
    ['--config', GetoptLong::REQUIRED_ARGUMENT], 
    ['--os', GetoptLong::REQUIRED_ARGUMENT ]
)

setup_os = ""
setup_image = ""
setup_config = ""

begin
  opts.each do |opt, arg|
    case opt
      when '--help'
        puts <<-EOF
vagrant [OPTION] ... CMD

-h, --help:
  show help

--config <demo|your_custom_config>:
  Used configuration. All configurations are located inside ./config/ folder

--os <suse|fedora>:
  Used linux distribution. 

CMD: 'up', 'destroy' or any other vagrant command

Example: vagrant --config=demo --os=suse up 

        EOF
        exit(0)
      when '--config'
        setup_config=arg
      when '--os'
        if arg == "suse" then
            setup_os = "suse"
            setup_image = "generic/opensuse15"
        else
            setup_os = "fedora"
            setup_image = "fedora/31-cloud-base"
        end
    end
  end
  rescue
end

if setup_config == "" then
  puts "Missing 'config' argument (try --help)"
  exit(0)
end

if setup_os == "" then
  puts "Missing 'os' argument (try --help)"
  exit(0)
end

$env_ip = ""
$with_password = setup_config != 'demo'

Vagrant.configure(2) do |config|
    
  env_config = File.read("config/#{setup_config}/env.yml")
  env_match = env_config.scan(/develop_ip:\s*"([^"]*)"/).last
  if env_match then
    $env_ip = env_match.first
  else
    raise "no 'develop_ip' found in file 'config/#{setup_config}/env.yml'"
  end
  
  print "Used ip address: #{$env_ip}\n"
  
  config.vm.define "smartserver", autostart: true do |setup|
    setup.vm.box = setup_image
    setup.ssh.username = 'vagrant'
    setup.ssh.password = 'vagrant'
    setup.ssh.insert_key = 'true'
    setup.vm.network "private_network", ip: $env_ip
    #setup.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    setup.vm.synced_folder ".", "/vagrant"
    setup.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", "2"]
    end
    
    if setup_os == 'fedora' then
        setup.vm.provision "ansible_local" do |ansible|
            ansible.limit = "all"
            ansible.playbook = "utils/fedora.yml"
            ansible.inventory_path = "config/#{setup_config}/server.ini"
            ansible.compatibility_mode = "2.0"
            ansible.provisioning_path = "/vagrant/"
            ansible.become = true
            ansible.become_user = "root"
            #ansible.raw_arguments = "--ask-vault-pass"
            #ansible.ask_vault_pass = true
        end  
    end  

    # Ask for vault password
    setup.vm.provision "shell", env: {"VAULT_PASS" => Environment.new}, inline: <<-SHELL
        echo "$VAULT_PASS" > /tmp/vault_pass
    SHELL

    if setup_os == 'suse' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo zypper --non-interactive install ansible python-xml
        SHELL
    else
        setup.vm.provision "shell", inline: <<-SHELL
        sudo yum --assumeyes install ansible python
        SHELL
    end
    
    setup.vm.provision "ansible_local" do |ansible|
      ansible.limit = "all"
      ansible.playbook = "server.yml"
      ansible.inventory_path = "config/#{setup_config}/server.ini"
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
      
      if setup_config != 'demo' then
        ansible.vault_password_file = "/tmp/vault_pass"
      end

      if setup_os == 'fedora' then
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
class Environment
    require 'socket'
    require 'timeout'
    require 'net/ssh'
    
    def to_s        
        print "check server reachability "
        
        begin
            #session = Net::SSH.start( '192.168.1.50', 'vagrant', password: "vagrant" )
            #session.close
            Socket.tcp($env_ip, 22, connect_timeout: 1) {}
            print " ok\n"
        rescue Exception => e #Errno::ECONNREFUSED, Errno::EHOSTUNREACH
            print "." # + e.message
            retry
        end

        pass = ""
        if $with_password then
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
        end
        pass
    end
end
