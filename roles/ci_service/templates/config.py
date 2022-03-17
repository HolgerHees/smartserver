server_host = "{{server_domain}}"

status_file = "{{global_tmp}}ci_service.status"

lib_dir = "{{global_lib}}ci_service/"
log_dir = "{{global_log}}ci_service/"
build_dir = "{{global_build}}"
repository_dir = "{{global_build}}ci_job"

repository_url = "{{vault_deployment_config_git}}"
access_token = "{{vault_deployment_token_git if vault_deployment_token_git != 'None' else ''}}"

service_ip = "127.0.0.1"
service_port = "8506"

deployments = [ { "config": "demo", "os": "suse" }, { "config": "demo", "os": "fedora" }, { "config": "demo", "os": "ubuntu" } ]
