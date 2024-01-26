camera_names = [ "{% for camera in camera_devices %}{{camera["ftp_upload_name"]}}{% if not loop.last %}", "{% endif %}{% endfor %}" ]

upload_path        = "/var/lib/camera_service/upload/"
cache_path        = "/var/lib/camera_service/cache/"

cache_user = {{system_users['www'].id}}
cache_group = {{system_groups['www'].id}}

preview_small_size = "400x300" # DPI == 1
preview_medium_size = "600x400" # DPI > 1
preview_mime = { "suffix": "jpg", "format": "jpeg" }
allowed_upload_suffixes = [".jpg",".jpeg",".png"]
