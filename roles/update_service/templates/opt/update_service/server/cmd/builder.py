from config import config
import logging

from server.cmd.workflow import CmdWorkflow


class CmdBuilder: 
    def __init__(self,dependency_watcher,process_watcher,system_update_watcher,deployment_state_watcher, operating_system):
        self.system_update_cmds = operating_system.getSystemUpdateCmds()
        
        self.dependency_watcher = dependency_watcher
        self.process_watcher = process_watcher
        self.system_update_watcher = system_update_watcher
        self.deployment_state_watcher = deployment_state_watcher

        self.cmd_type_check_type_mapping = {
            None:             "update_check",
            "system_update":  "system_update_check",
            "deployment_update":  "deployment_update_check",
            "process_update":  "process_check"
        }

    def buildCmd(self, cmd, interaction, cwd, env ):
        return { "cmd": cmd, "interaction": interaction, "cwd": cwd, "env": env }
      
    def buildFunction(self, function, *args, **kwargs ):
        return { "function": function, "args": args, "kwargs": kwargs }

    def buildCmdBlock(self, username, cmd_type, cmds ):
        return { "username": username, "cmd_type": cmd_type, "cmds": cmds }
      
    def buildFunctionBlock(self, username, function, params ):
        return { "username": username, "function": function, "params": params }

    def buildProcessWatcherFunction(self, is_cleanup):
        return self.buildFunction("process_watcher.cleanup" if is_cleanup else "process_watcher.refresh" )

    def buildSoftwareVersionCheckCmd(self, check_type):
        return self.buildCmd(config.cmd_software_version_check, interaction=None,cwd=None,env=None)

    def buildSoftwareVersionCheckCmdBlock(self, username):
        cmd = self.buildSoftwareVersionCheckCmd(None)
        return self.buildCmdBlock(username, "software_check", [cmd])

    def buildSystemUpdateCheckCmd(self, check_type):
        cmd = u"{}{}".format(config.cmd_system_update_check, " --limit={}".format(check_type) if check_type else "")
        return self.buildCmd(cmd, interaction=None,cwd=None,env=None)
      
    def buildSystemUpdateCheckBlock(self, username, check_type):
        cmds = []
        if check_type != "process_update":
            cmds.append( self.buildSystemUpdateCheckCmd(check_type) )
        if check_type is None or check_type == "process_update":
            cmds.append( self.buildProcessWatcherFunction(False) )
        return self.buildCmdBlock(username, self.cmd_type_check_type_mapping[check_type], cmds)

    def buildSystemRebootCmdBlock(self, username):
        cmds = []
        cmds.append( self.buildCmd(config.cmd_request_reboot, interaction=None,cwd=None,env=None) )
        cmds.append( self.buildProcessWatcherFunction(False) ) # needs to be refreshed, because sometimes reboot state is still true right after reboot
        return self.buildCmdBlock(username, "system_reboot", cmds)

    def buildSystemRebootCmdBlockIfNecessary(self, username,params):
        if self.system_update_watcher.isRebootNeeded():
            return self.buildSystemRebootCmdBlock(username)
        return None

    def buildRestartDaemonCmdBlock(self, username):
        cmds = []
        cmds.append( self.buildCmd("{} update_service".format(config.cmd_service_restart), interaction=None,cwd=None,env=None) )
        return self.buildCmdBlock(username, "daemon_restart", cmds)

    def buildRestartDaemonCmdBlockIfNecessary(self, username,params):
        is_update_service_oudated = self.process_watcher.isUpdateServiceOutdated()
        if is_update_service_oudated:
            return self.buildRestartDaemonCmdBlock(username)

        return None

    def buildRestartServiceCmdBlock(self, username, services):
        cmds = []
        cmds.append( self.buildCmd("{} {}".format(config.cmd_service_restart, services.replace(","," ")), interaction=None,cwd=None,env=None) )
        cmds.append( self.buildProcessWatcherFunction(True) )
        return self.buildCmdBlock(username, "service_restart", cmds)

    def buildRestartServiceCmdBlockIfNecessary(self, username,params):
        outdated_services = self.process_watcher.getOutdatedServices()
        if len(outdated_services) > 0:
            return self.buildRestartServiceCmdBlock(username,",".join(outdated_services))

        return None
          
    def buildInstallSystemUpdateCmdBlock(self, username):
        cmds = []
        cmds.append( self.buildFunction("dependency_watcher.checkSmartserverSystemUpdateDependedRoles") )
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

            cmds = []
            cmds.append( self.buildFunction("dependency_watcher.checkSmartserverSmartserverUpdateDependedRoles", tags = tags) )
            cmds.append( self.buildCmd(cmd_deploy_system, interaction=interaction,cwd=config.deployment_directory,env={"ANSIBLE_FORCE_COLOR": "1","ANSIBLE_CONFIG": "ansible_us.cfg"}) )
            cmds.append( self.buildSystemUpdateCheckCmd("deployment_update") )
            cmds.append( self.buildCmd(config.cmd_container_cleanup, interaction=None,cwd=None,env=None) )
            return self.buildCmdBlock(username, "deployment_update", cmds)
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
    
    def validateUpdateHashes(self,username,params):
        checks = []
        if params["system_updates_hash"]:
            #logging.info(params["system_updates_hash"])
            #logging.info(self.system_update_watcher.getSystemUpdatesHash())
            if params["system_updates_hash"] != self.system_update_watcher.getSystemUpdatesHash():
                checks.append(CmdWorkflow.STATE_CHECK_WRONG_SYSTEM_UPDATE_STATE)

        if params["smartserver_changes_hash"]:
            #logging.info(params["smartserver_changes_hash"])
            #logging.info(self.system_update_watcher.getSmartserverChangesHash())
            if params["smartserver_changes_hash"] != self.system_update_watcher.getSmartserverChangesHash():
                checks.append(CmdWorkflow.STATE_CHECK_WRONG_SMARTSERVER_UPDATE_STATE)
                
        if len(checks) > 0:
            return ",".join(checks)
        else:
            return True
