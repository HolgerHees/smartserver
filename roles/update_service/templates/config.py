cmd_software_version_check = "/opt/update_service/env/bin/python3 /opt/update_service/software_version_check"
cmd_system_update_check = "/opt/update_service/env/bin/python3 /opt/update_service/system_update_check"
cmd_service_restart = "systemctl restart"
cmd_request_reboot = "reboot"
cmd_container_cleanup = "/opt/container/clean_images -q"

software_check_email = {{ "'" + update_service_software_check_email + "'" if update_service_software_check_email is defined else 'None'}}
update_check_email = {{ "'" + update_service_system_check_email + "'" if update_service_system_check_email is defined else 'None'}}

server_host = "{{server_domain}}"

service_ip = "127.0.0.1"
service_port = "8505"

target_dir = "{{global_lib}}update_service/"
build_dir = "{{global_build}}"
htdocs_dir = "{{htdocs_path}}"

components_config_dir = "{{global_etc}}update_service/software/"
dependencies_config_dir = "{{global_etc}}update_service/dependencies/"

outdated_roles_state_dir = "{}outdated_roles/".format(target_dir)

software_version_state_file = "{}software_versions.state".format(target_dir)
system_update_state_file = "{}system_updates.state".format(target_dir)

deployment_state_file = "{}deployment.state".format(target_dir)
deployment_tags_file = "{}deployment.tags".format(target_dir)

deployment_workflow_file = "{{global_tmp}}update_service.workflow".format(target_dir)

deployment_config_path = "{{deployment_config_path}}"
deployment_inventory_path = "{{deployment_inventory_path}}"
deployment_directory = "{{deployment_path}}"

git_remote = "{{deployment_config_git}}"

global_config = { 
  "github_auth_token": "{{github_auth_token if github_auth_token is defined else ''}}"
}

os_type = "{{os_type}}"

job_state_file = "{{global_tmp}}update_service.state"
job_log_folder = "{{global_log}}update_service/"
