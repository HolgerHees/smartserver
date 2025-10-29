require 'getoptlong'

opts = GetoptLong.new(
    ['--help', '-h', GetoptLong::NO_ARGUMENT ],
    ['--config', GetoptLong::REQUIRED_ARGUMENT], 
    ['--os', GetoptLong::REQUIRED_ARGUMENT ],
    ['--ansible', GetoptLong::OPTIONAL_ARGUMENT ],
    ['--color', GetoptLong::OPTIONAL_ARGUMENT ],
    ['--force', GetoptLong::OPTIONAL_ARGUMENT ]
)

setup_os = ""
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

--os <suse|alma|ubuntu>:
  Used linux distribution. 
  
  <suse>      : openSUSE Leap 15.6 (opensuse/Leap-15.6.x86_64)
  <alma>      : AlmaLinux 9.1 (almalinux/9)
  <ubuntu>    : Ubuntu 24.04 (bento/ubuntu-24.04)

--ansible [-vvv]:
  Optional argument to provide additional parameters for ansible. 

CMD: 'up', 'destroy' or any other vagrant command

Example: vagrant --config=demo --os=suse up 

        EOF
        exit(0)
      when '--config'
        setup_config=arg
      when '--os'
        if arg == "testsuse" then
            setup_os = "suse"
            setup_image = "bento/opensuse-leap-16.0"
            setup_version = "202510.26.0"
        elsif arg == "testalma" then
            setup_os = "alma"
            setup_image = "almalinux/9"
            setup_version = "9.6.20250522"
        elsif arg == "suse" then
            setup_os = "suse"
            setup_image = "opensuse/Leap-15.6.x86_64"
            setup_version = "15.6.13.356"
        elsif arg == "ubuntu" then
            setup_os = "ubuntu"
            setup_image = "bento/ubuntu-24.04"
            setup_version = "202510.26.0"
        elsif arg == "alma" then
            setup_os = "alma"
            setup_image = "almalinux/9"
            setup_version = "9.1.20221117"
            #setup.vm.box_version = "9.2.20230513" => has broken vboxadd.service
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
    setup.vm.box_version = setup_version

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

    # mitogen preparation
    #mitogen_config = File.read("roles/deployment/tasks/main.yml")
    #mitogen_match = mitogen_config.scan(/mitogen_version:\s*'([^']*)'/).last
    #$mitogen_version = mitogen_match.first
    #setup.vm.provision "shell" do |s|
    #  s.inline = <<-SHELL
    #    if [ ! -d "/opt/mitogen" ]; then
    #      echo "Download and install mitogen #{$mitogen_version}"
    #      cp /vagrant/roles/deployment/templates/ansible.cfg /vagrant/ansible.cfg
    #      curl -s -L https://github.com/mitogen-hq/mitogen/archive/refs/tags/v#{$mitogen_version}.tar.gz | tar xvz -C /opt/ > /dev/null
    #      cd /opt/; ln -s mitogen-0.3.3 mitogen
    #    else
    #      echo "Mitogen #{$mitogen_version} already installed"
    #    fi
    #  SHELL
    #end

    #setup.vm.network :public_network, :bridge => 'enp3s0',:use_dhcp_assigned_default_route => true
    setup.vm.synced_folder ".", "/vagrant"
    #, automount: true

    cpus = `/usr/bin/nproc`.to_i
    if cpus < 2 then
        cpus = 2
    else
        cpus = (cpus / 3).floor()
    end

    setup.vm.provider :virtualbox do |vb|
        vb.name = $image_name
        vb.customize ["modifyvm", :id, "--memory", "6144"]
        vb.customize ["modifyvm", :id, "--cpus", cpus]
        #vb.customize ["natnetwork", "add", "--netname", "smartserver", "--network", "#{$env_ip}/24", "--enable"]
        #vb.customize ["modifyvm", :id, "--nic2", "natnetwork"]
    end

    setup.vm.provider "hyperv" do |hv|
        hv.vmname = $image_name
        hv.memory = 6144
        hv.cpus = cpus
    end
    #setup.vm.provider "vmware_desktop" do |vw|
    #  vw.vmx["memsize"] = "6144"
    #  vw.vmx["numvcpus"] = cpus
    #end
    
    require 'time'
    offset = ((Time.zone_offset(Time.now.zone) / 60) / 60)
    # offset needs to be inverted => https://stackoverflow.com/questions/49916815/strange-timezone-etc-gmt-1-in-firefox
    timezone_suffix = offset >= 0 ? "-#{offset.to_s}" : "+#{offset.to_s}"
    timezone = 'Etc/GMT' + timezone_suffix
    setup.vm.provision :shell, :inline => "sudo rm /etc/localtime && sudo ln -s /usr/share/zoneinfo/" + timezone + " /etc/localtime", run: "always"

    setup.vm.network "private_network", ip: $env_ip

    # Ask for vault password
    password = Environment.getPassword()
   
    if setup_os == 'suse' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo zypper --non-interactive install python3-netaddr python3-pip system-user-nobody
        sudo pip install ansible==4.10.0
        SHELL
    elsif setup_os == 'ubuntu' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo apt-get update
        sudo apt-get -y install python3-netaddr python3-pip
        sudo pip install ansible==9.8.0 --break-system-packages
        SHELL
    elsif setup_os == 'alma' then
        setup.vm.provision "shell", inline: <<-SHELL
        sudo yum --assumeyes install python python3-netaddr python3-pip
        sudo pip install --prefix=/usr/ ansible==8.7.0
        # is needed to avoid that 'dnf-makecache.timer' is running during deployemnt. Could result in failed 'dnf-makecache.service' because of restarted named container
        sudo systemctl stop dnf-makecache.timer
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
      ansible.galaxy_role_file = "requirements.yml"
      ansible.raw_arguments = setup_ansible
      ansible.install = false
      if setup_config != 'demo' then
        ansible.vault_password_file = "/tmp/vault_pass"
      end

      #if setup_os == 'fedora' and setup_image.end_with?('cloud-base') then
      #  ansible.become = true
      #  ansible.become_user = "root"
      #end
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
