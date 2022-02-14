software_check_email = {{ "'" + update_service_software_check_email + "'" if update_service_software_check_email != 'None' else 'None'}}
update_check_email = {{ "'" + update_service_system_check_email + "'" if update_service_system_check_email != 'None' else 'None'}}

server_host = "{{server_domain}}"

service_ip = "{{server_name}}"

target_dir = "{{global_lib}}update_service/"

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

git_remote = "{{vault_deployment_config_git}}"

global_config = { 
  "github_access_token": "{{vault_deployment_token_git if vault_deployment_token_git != 'None' else ''}}"
}

os_type = "{{os_type}}"

job_state_file = "{{global_tmp}}update_service.state"
job_log_folder = "{{global_log}}update_service/"
