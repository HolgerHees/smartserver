server_host = "{{server_domain}}"

status_file = "/tmp/ci_service/ci_service.status"

lib_dir = "/var/lib/ci_service/"
log_dir = "/var/log/ci_service/"
repository_dir = "/opt/ci_job/"

repository_url = "{{deployment_config_git}}"
auth_token = "{{github_auth_token if github_auth_token is defined else ''}}"

branch = "master"

deployments = [ { "config": "demo", "os": "suse" }, { "config": "demo", "os": "alma" }, { "config": "demo", "os": "ubuntu" } ]
