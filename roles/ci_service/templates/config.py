server_host = "{{server_domain}}"

status_file = "{{global_tmp}}ci_service.status"

lib_dir = "{{global_lib}}ci_service/"
log_dir = "{{global_log}}ci_service/"
repository_dir = "{{global_build}}ci_job/"

repository_url = "{{deployment_config_git}}"
auth_token = "{{github_auth_token if github_auth_token is defined else ''}}"

branch = "master"

service_ip = "127.0.0.1"
service_port = "8506"

deployments = [ { "config": "demo", "os": "suse" }, { "config": "demo", "os": "alma" }, { "config": "demo", "os": "ubuntu" } ]
