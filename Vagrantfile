require 'getoptlong'

opts = GetoptLong.new(
    [ '--help', '-h', GetoptLong::NO_ARGUMENT ],
    ['--config', GetoptLong::REQUIRED_ARGUMENT], 
    ['--os', GetoptLong::REQUIRED_ARGUMENT ],
    ['--ansible', GetoptLong::OPTIONAL_ARGUMENT ]
)

setup_os = ""
setup_version = ""
setup_image = ""
setup_config = ""
setup_ansible = ""

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
  
  <suse>   : openSUSE Leap 15.3 (bento/opensuse-leap-15.3)
  <fedora> : Fedora 35 Server (fedora/35-cloud-base)
  <ubuntu> : Ubuntu 21.10 (ubuntu/impish64)

--ansible [-vvv]:
  Optional argument to provide additional parameters for ansible. 

CMD: 'up', 'destroy' or any other vagrant command

Example: vagrant --config=demo --os=suse up 

        EOF
        exit(0)
      when '--config'
        setup_config=arg
      when '--os'
        if arg == "suse" then
            setup_os = "suse"
            #setup_version = "15.2"
            #setup_image = "bento/opensuse-leap-" + setup_version
            setup_version = "15.3"
            setup_image = "opensuse/Leap-" + setup_version + ".x86_64"
        elsif arg == "ubuntu" then
            setup_os = "ubuntu"
            #setup_version = "20.04"
            #setup_image = "ubuntu/focal64"
            setup_version = "21.04"
            setup_image = "ubuntu/impish64"
        elsif arg == "fedora" then
            setup_os = "fedora"
            setup_version = "35"
            setup_image = "fedora/" + setup_version + "-cloud-base"
        end
      when '--ansible'
        setup_ansible=arg
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
#$is_reboot_possible = false
$image_name = "smartserver_" + setup_config + "_" + setup_os

Vagrant.configure(2) do |config|
    
  env_config = File.read("config/#{setup_config}/env.yml")
  env_match = env_config.scan(/staging_ip:\s*"([^"]*)"/).last
  if env_match then
    $env_ip = env_match.first
  else
    raise "no 'staging_ip' found in file 'config/#{setup_config}/env.yml'"
  end
  
  print "Used ip address: #{$env_ip}\n"
  
  config.vm.define $image_name, autostart: true do |setup|
    setup.vm.box = setup_image
    setup.ssh.username = 'vagrant'
    #setup.ssh.password = 'vagrant'
    setup.ssh.insert_key = 'true'
    
    if File.exist?("#{Dir.home}/.ssh/id_rsa.pub") then
        setup.vm.provision "shell" do |s|
            ssh_pub_key = File.readlines("#{Dir.home}/.ssh/id_rsa.pub").first.strip
            s.inline = <<-SHELL
              echo #{ssh_pub_key} >> /home/vagrant/.ssh/authorized_keys
              mkdir -p /root/.ssh && touch /root/.ssh/authorized_keys
              echo #{ssh_pub_key} >> /root/.ssh/authorized_keys
            SHELL
        end
    end
    
    setup.vm.network "private_network", ip: $env_ip
    #setup.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    setup.vm.synced_folder ".", "/vagrant"
    #, automount: true

    setup.vm.provider :virtualbox do |vb|
        vb.name = $image_name
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", "2"]
    end

    setup.vm.provider "hyperv" do |hv|
        hv.vmname = $image_name
        hv.memory = 6144
        hv.cpus = 2
    end
    #setup.vm.provider "vmware_desktop" do |vw|
    #  vw.vmx["memsize"] = "6144"
    #  vw.vmx["numvcpus"] = "2"
    #end
    
    require 'time'
    offset = ((Time.zone_offset(Time.now.zone) / 60) / 60)
    # offset needs to be inverted => https://stackoverflow.com/questions/49916815/strange-timezone-etc-gmt-1-in-firefox
    timezone_suffix = offset >= 0 ? "-#{offset.to_s}" : "+#{offset.to_s}"
    timezone = 'Etc/GMT' + timezone_suffix
    setup.vm.provision :shell, :inline => "sudo rm /etc/localtime && sudo ln -s /usr/share/zoneinfo/" + timezone + " /etc/localtime", run: "always"

    # Ask for vault password
    password = Environment.getPassword()
   
    if setup_os == 'suse' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo zypper --non-interactive install python3-netaddr python3-pip system-user-nobody
        sudo pip install ansible==2.10.7
        SHELL
    elsif setup_os == 'ubuntu' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo apt-get update
        sudo apt-get -y install python3-netaddr python3-pip
        sudo pip install ansible==2.10.7
        SHELL
    elsif setup_os == 'fedora' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo yum --assumeyes install python python3-netaddr python3-pip
        sudo pip install ansible==2.10.7
        SHELL
    else
        print "*** not supported ***"
        return
    end  

    #if $is_reboot_possible and (setup_os != 'fedora' or !setup_image.end_with?('cloud-base')) then
    #    setup.vm.provision "shell", inline: <<-SHELL
    #    sudo mount -t vboxsf -o uid=$UID,gid=$(id -g) vagrant /vagrant
    #    SHELL
    #end

    setup.vm.provision "shell", env: {"VAULT_PASS" => password }, inline: <<-SHELL
        echo "$VAULT_PASS" > /tmp/vault_pass
    SHELL
    
    setup.vm.provision "ansible_local" do |ansible|
      ansible.limit = "all"
      ansible.playbook = "server.yml"
      ansible.inventory_path = "config/#{setup_config}/server.ini"
      ansible.compatibility_mode = "2.0"
      ansible.provisioning_path = "/vagrant/"
      ansible.raw_arguments = setup_ansible
      ansible.install = false
      if setup_config != 'demo' then
        ansible.vault_password_file = "/tmp/vault_pass"
      end

      if setup_os == 'fedora' and setup_image.end_with?('cloud-base') then
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

module Environment
#  require 'socket'
#  require 'timeout'
#  require 'net/ssh'
  
#  # Reachability check
#  def self.checkReachability
#      
#      def to_s       
#          sleep(0.5) # give server time to initiate reboot#

#          print "check server reachability "
          
#          begin
#              #session = Net::SSH.start( '192.168.1.50', 'vagrant', password: "vagrant" )
#              #session.close
#              Socket.tcp($env_ip, 22, connect_timeout: 1) {}
#              print " ok\n"
#          rescue Exception => e #Errno::ECONNREFUSED, Errno::EHOSTUNREACH
#              print "." # + e.message
#              retry
#          end
#          ""
#      end
#  end

  # Password Input Function
  def self.getPassword
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
