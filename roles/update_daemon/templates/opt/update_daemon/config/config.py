send_software_version_notification = {{'True' if send_update_notifier_email else 'False'}}
send_system_update_notification = {{'True' if send_update_notifier_email else 'False'}}

server_host = "{{server_domain}}"

target_dir = "{{global_lib}}update_daemon/"
components_config_dir = "{{global_etc}}update_daemon/software/"

software_version_state_file = "{}software_versions.state".format(target_dir)
system_update_state_file = "{}system_updates.state".format(target_dir)
deployment_state_file = "{}deployment.state".format(target_dir)

global_config = { 
  "github_access_token": "{{vault_deployment_token_git}}"
}

os_type = "{{os_type}}"
