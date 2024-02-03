#!/usr/bin/python3

import fcntl
import os
import sys
import importlib
import subprocess
import time
import datetime

from smartserver.command import exec2
from smartserver.argsparser import ArgsParser

from config import config

job_config = None

def logInfo(msg):
    if job_config is not None:
        print("{}: {}".format(job_config.name.upper(), msg))
    else:
        print(msg)
    sys.stdout.flush()

def logError(msg):
    if job_config is not None:
        print("{}: {}".format(job_config.name.upper(), msg, file=sys.stderr))
    else:
        print(msg, file=sys.stderr)
    sys.stderr.flush()

def loadJobConfig():
    args_cfg = { "job": None }
    args_values = ArgsParser.parse(args_cfg,sys.argv)

    if not args_values["job"]:
        return [None, "Please specify a job"]

    try:
        job_config = importlib.import_module("config.jobs.{}".format(args_values["job"]))
        return [job_config, None]
    except ModuleNotFoundError:
        return [None, "Job '{}' not found".format(args_values["job"])]

def validateSourceAndDestination(config, job_config):
    is_remote = job_config.destination[0:1] != '/'
    if is_remote:
        rclone_config = "{}rclone/{}.config".format(config.config_dir,job_config.name)
        if not os.path.exists(rclone_config):
            return [None, None, "No configuration '{}' for non local destination '{}' found".format(rclone_config, job_config.destination)]
    else:
        rclone_config = None
        with open("/etc/fstab") as f:
            fstab_data = f.read()
            path = job_config.destination
            while path != '/':
                #print(path)
                if path in fstab_data:
                    logInfo("Check mountpoint '{}'".format(path))
                    result = subprocess.run(["/usr/bin/mountpoint", path], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    if result.returncode != 0:
                        return [None, None, "Mountpoint '{}' not mounted".format(path)]
                    break
                path = os.path.dirname(path)

    for source in job_config.sources:
        if not os.path.exists(source["path"]):
            logError()
            return [None, None, "Source path '{}' does not exist".format(source["path"])]

    return [is_remote, rclone_config, None]

def prepareBackupCommand(config, job_config):
    backup_env = {"PATH": "/usr/bin/"}
    backup_cmd = [config.rclone_cmd, "--one-file-system", "--links", "--log-level", "INFO"]
    #backup_cmd.append("--copy-links")

    if job_config.bandwidth_limit:
        backup_cmd.append("--bwlimit")
        backup_cmd.append(job_config.bandwidth_limit)

    if rclone_config:
        backup_cmd.append("--config=\"{}\"".format(rclone_config))

    if job_config.password:
        result = subprocess.run([config.rclone_cmd, "obscure", job_config.password], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            return [None, None, "Obscuration of password failed\n" + result.stdout]

        password = result.stdout.strip()

        backup_env["RCLONE_CONFIG_BACKUP_TYPE"] = "crypt"
        backup_env["RCLONE_CONFIG_BACKUP_FILENAME_ENCRYPTION"] = "standard"
        backup_env["RCLONE_CONFIG_BACKUP_DIRECTORY_NAME_ENCRYPTION"] = "true"
        backup_env["RCLONE_CONFIG_BACKUP_PASSWORD"] = password
    else:
        backup_cmd.append("sync")

    backup_cmd.append("--local-no-check-updated")

    return [backup_env, backup_cmd, None]

def prepareSourceBackupCommand(job_config, backup_cmd):
    sync_backup_cmd = backup_cmd.copy()

    # non encrypted local backups can skip checksum check for performance reasons
    #if not is_remote:
    #    backup_cmd.append("--ignore-checksum")

    destination = job_config.destination
    if not destination.endswith(os.path.sep):
        destination += os.path.sep
    if source["name"]:
        destination += source["name"] + os.path.sep

    logfile = job_config.logfile.replace("[DATETIME]", datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    #logfile = job_config.logfile.replace("[DATETIME]", "")

    sync_backup_cmd.append("--log-file")
    sync_backup_cmd.append(logfile)

    #if source["excludes"]:
    #    for exclude in source["excludes"]:
    #        sync_backup_cmd.append("--exclude")
    #        sync_backup_cmd.append(prepareFilterTerm(exclude))

    #if source["includes"]:
    #    for include in source["includes"]:
    #        sync_backup_cmd.append("--include")
    #        sync_backup_cmd.append(prepareFilterTerm(include))

    if source["filter"]:
        for filter in source["filter"]:
            sync_backup_cmd.append("--filter")
            sync_backup_cmd.append(filter)

    if source["options"]:
        for option in source["options"]:
            sync_backup_cmd.append(option)

    if job_config.password:
        sync_backup_cmd.append("--crypt-remote")
        sync_backup_cmd.append(destination)
        sync_backup_cmd.append("sync")
        sync_backup_cmd.append(source["path"])
        sync_backup_cmd.append("backup:")
    else:
        sync_backup_cmd.append(source["path"])
        sync_backup_cmd.append(destination)

    return sync_backup_cmd

job_config, error_message = loadJobConfig()
if error_message:
    logError(error_message)
    exit(1)

is_remote, rclone_config, error_message = validateSourceAndDestination(config, job_config)
if error_message:
    logError(error_message)
    exit(1)

backup_env, backup_cmd, error_message = prepareBackupCommand(config, job_config)
if error_message:
    logError(error_message)
    exit(1)

with open(job_config.lockfile, "w") as f:
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)

        start = time.time()
        logInfo("Starting backup sync")
        for source in job_config.sources:
            sync_backup_cmd = prepareSourceBackupCommand(job_config, backup_cmd)
            #print(sync_backup_cmd)

            result = subprocess.run(sync_backup_cmd, env=backup_env, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
                end = time.time()
                duration = datetime.timedelta(seconds=round(end - start))
                logError("Backup sync failed after {}".format(duration))
                logError(result.stdout)
                exit(1)

        fcntl.flock(lock_file_fd, fcntl.LOCK_UN)

        end = time.time()
        duration = datetime.timedelta(seconds=round(end - start))
        logInfo("Backup sync finished after {}".format(duration))
    except IOError:
        logInfo("Sync already running")
