from config import config


class CmdBuilder: 
    def __init__(self,logger,dependency_watcher,process_watcher,system_update_watcher,deployment_state_watcher, operating_system):
        self.logger = logger
        
        self.system_update_cmds = operating_system.getSystemUpdateCmds()
        
        self.dependency_watcher = dependency_watcher
        self.process_watcher = process_watcher
        self.system_update_watcher = system_update_watcher
        self.deployment_state_watcher = deployment_state_watcher

        self.cmd_software_version_check = "/opt/update_service/software_version_check"
        self.cmd_system_update_check = "/opt/update_service/system_update_check"
        self.cmd_service_restart = "systemctl restart"
        self.cmd_request_reboot = "reboot"
        self.cmd_check_reboot = "runlevel | grep \"6\""
        self.cmd_container_cleanup = "/opt/docker/cleanup -q"
        
        self.cmd_type_check_type_mapping = {
            None:             "update_check",
            "system_update":  "system_update_check",
            "deployment_update":  "deployment_update_check",
            "process_update":  "process_check"
        }

    def buildCmd(self, cmd, interaction, cwd, env ):
        return { "cmd": cmd, "interaction": interaction, "cwd": cwd, "env": env }
      
    def buildFunction(self, function ):
        return { "function": function }

    def buildCmdBlock(self, username, cmd_type, cmds ):
        return { "username": username, "cmd_type": cmd_type, "cmds": cmds }
      
    def buildFunctionBlock(self, username, function, params ):
        return { "username": username, "function": function, "params": params }

    def buildProcessWatcherFunction(self, is_cleanup):
        return self.buildFunction("process_watcher.cleanup" if is_cleanup else "process_watcher.refresh" )

    def buildSoftwareVersionCheckCmd(self, check_type):
        return self.buildCmd(self.cmd_software_version_check, interaction=None,cwd=None,env=None)

    def buildSoftwareVersionCheckCmdBlock(self, username):
        cmd = self.buildSoftwareVersionCheckCmd(None)
        return self.buildCmdBlock(username, "software_check", [cmd])

    def buildSystemUpdateCheckCmd(self, check_type):
        cmd = u"{}{}".format(self.cmd_system_update_check, " --limit={}".format(check_type) if check_type else "")
        return self.buildCmd(cmd, interaction=None,cwd=None,env=None)
      
    def buildSystemUpdateCheckBlock(self, username, check_type):
        cmds = []
        if check_type != "process_update":
            cmds.append( self.buildSystemUpdateCheckCmd(check_type) )
        if check_type is None or check_type == "process_update":
            cmds.append( self.buildProcessWatcherFunction(False) )
        return self.buildCmdBlock(username, self.cmd_type_check_type_mapping[check_type], cmds)

    def buildSystemRebootCmdBlock(self, username):
        cmd = self.buildCmd(self.cmd_request_reboot, interaction=None,cwd=None,env=None)
        # no state refresh needed, outdated processes and reboot state is loaded during service startup
        return self.buildCmdBlock(username, "system_reboot", [cmd])

    def buildSystemRebootCmdBlockIfNecessary(self, username,params):
        if self.system_update_watcher.isRebootNeeded():
            return self.buildSystemRebootCmdBlock(username)
        return None

    def buildRestartDaemonCmdBlock(self, username):
        cmd_daemon_restart = "{} update_service".format(self.cmd_service_restart)
        cmd = self.buildCmd(cmd_daemon_restart, interaction=None,cwd=None,env=None)
        return self.buildCmdBlock(username, "daemon_restart", [cmd])

    def buildRestartDaemonCmdBlockIfNecessary(self, username,params):
        is_update_service_oudated = self.process_watcher.isUpdateServiceOutdated()
        if is_update_service_oudated:
            return self.buildRestartDaemonCmdBlock(username)

        return None

    def buildRestartServiceCmdBlock(self, username, services):
        self.cmd_service_restart_with_services = "{} {}".format(self.cmd_service_restart, services.replace(","," "))
        
        restart_service_cmd = self.buildCmd(self.cmd_service_restart_with_services, interaction=None,cwd=None,env=None)
        refresh_process_watcher_cmd = self.buildProcessWatcherFunction(True)
        
        return self.buildCmdBlock(username, "service_restart", [restart_service_cmd,refresh_process_watcher_cmd])

    def buildRestartServiceCmdBlockIfNecessary(self, username,params):
        outdated_services = self.process_watcher.getOutdatedServices()
        if len(outdated_services) > 0:
            return self.buildRestartServiceCmdBlock(username,",".join(outdated_services))

        return None
          
    def buildInstallSystemUpdateCmdBlock(self, username):
        cmds = []
        cmds.append( self.buildFunction("dependency_watcher.checkSmartserverRoles") )
        for cmd in self.system_update_cmds:
            cmds.append( self.buildCmd(cmd, interaction=None,cwd=None,env=None) )
            
        cmds.append( self.buildProcessWatcherFunction(False) )
        cmds.append( self.buildSystemUpdateCheckCmd("system_update") )

        return self.buildCmdBlock(username, "system_update", cmds)

    def buildInstallSystemUpdateCmdBlockIfNecessary(self, username,params):
        updates = self.system_update_watcher.getSystemUpdates()
        if len(updates) > 0:
            return self.buildInstallSystemUpdateCmdBlock(username)
        return None

    def buildDeploymentSmartserverUpdateCmdBlock(self, username, password, tags):
        if not self.deployment_state_watcher.hasEncryptedVault() or password:
            cmd_deploy_system = "ansible-playbook -i {}".format(config.deployment_inventory_path)
            if password:
                cmd_deploy_system = "{} --ask-vault-pass".format(cmd_deploy_system) 
                interaction = {"Vault password:": "{}\n".format(password)}
            else:
                interaction = None
            if len(tags) > 0:
                cmd_deploy_system = "{} --tags \"{}\"".format(cmd_deploy_system,",".join(tags)) 
            cmd_deploy_system = "{} server.yml".format(cmd_deploy_system)

            cmd = self.buildCmd(cmd_deploy_system, interaction=interaction,cwd=config.deployment_directory,env={"ANSIBLE_FORCE_COLOR": "1"})
            post_cmd = self.buildSystemUpdateCheckCmd("deployment_update")
            clean_cmd = self.buildCmd(self.cmd_container_cleanup, interaction=None,cwd=None,env=None)
            return self.buildCmdBlock(username, "deployment_update", [cmd,post_cmd,clean_cmd])
        else:
            return None

    def buildDeploymentSmartserverUpdateCmdBlockIfNecessary(self, username,params):
        smartserver_changes = self.system_update_watcher.getSmartserverChanges()
        outdated_roles = self.dependency_watcher.getOutdatedRoles()
        
        if len(outdated_roles) > 0 or len(smartserver_changes) > 0:
            tags = outdated_roles if len(smartserver_changes) == 0 else []
            password = params["password"] if "password" in params else None
            return self.buildDeploymentSmartserverUpdateCmdBlock(username, password, tags)
        return None
