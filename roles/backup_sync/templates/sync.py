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

def prepareCommandEnv(config, job_config, rclone_config):
    env = {"PATH": "/usr/bin/"}
    if job_config.password:
        result = subprocess.run([config.rclone_cmd, "obscure", job_config.password], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            return [None, "Obscuration of password failed\n" + result.stdout]

        password = result.stdout.strip()

        env["RCLONE_CONFIG_BACKUP_TYPE"] = "crypt"
        env["RCLONE_CONFIG_BACKUP_FILENAME_ENCRYPTION"] = "standard"
        env["RCLONE_CONFIG_BACKUP_DIRECTORY_NAME_ENCRYPTION"] = "true"
        env["RCLONE_CONFIG_BACKUP_PASSWORD"] = password
    return [ env, None ]

def getDestination(job_config, source_config):
    destination = job_config.destination
    if not destination.endswith(os.path.sep):
        destination += os.path.sep
    if source_config["name"]:
        destination += source_config["name"] + os.path.sep
    return destination

def prepareSourceRestoreCommand(source_config, job_config, rclone_config):
    cmd = [config.rclone_cmd, "--one-file-system", "--links", "--log-level", "INFO"]

    if rclone_config:
        cmd.append("--config=\"{}\"".format(rclone_config))

    destination = getDestination(job_config, source_config)
    if job_config.password:
        cmd.append("--crypt-remote")
        cmd.append(destination)
        destination = "backup:"

    cmd.append("sync")
    cmd.append(destination)
    cmd.append("<YOUR_TARGET>")

    return cmd

def prepareSourceBackupCommand(is_single_source, index, source_config, job_config, rclone_config):
    cmd = [config.rclone_cmd, "--one-file-system", "--links", "--log-level", "INFO"]

    if rclone_config:
        cmd.append("--config=\"{}\"".format(rclone_config))

    if job_config.bandwidth_limit:
        cmd.append("--bwlimit")
        cmd.append(job_config.bandwidth_limit)

    index_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not is_single_source:
        index_name = "{}_{}".format(source_config["name"] if source_config["name"] else "source{}".format(index), index_name)
    logfile = job_config.logfile.replace("[INDEX]", index_name)

    cmd.append("--log-file")
    cmd.append(logfile)

    if source_config["filter"]:
        for filter in source_config["filter"]:
            cmd.append("--filter")
            cmd.append(filter)

    if source_config["options"]:
        for option in source_config["options"]:
            cmd.append(option)

    destination = getDestination(job_config, source_config)
    if job_config.password:
        cmd.append("--crypt-remote")
        cmd.append(destination)
        destination = "backup:"

    cmd.append("sync")
    cmd.append(source_config["path"])
    cmd.append(destination)

    return cmd

job_config, error_message = loadJobConfig()
if error_message:
    logError(error_message)
    exit(1)

is_remote, rclone_config, error_message = validateSourceAndDestination(config, job_config)
if error_message:
    logError(error_message)
    exit(1)


cmd_env, error_message = prepareCommandEnv(config, job_config, rclone_config)
if error_message:
    logError(error_message)
    exit(1)

with open(job_config.lockfile, "w") as lock_file_fd:
    try:
        fcntl.flock(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        start = time.time()
        logInfo("Starting backup sync")
        #for source_config in job_config.sources:
        #    ['/opt/backup_sync/bin/rclone', '--links', '--log-level', 'INFO', '--crypt-remote', '/dataRaid/cloud/remote/pbolle/data/', 'sync', 'backup:', '<YOUR_TARGET>']

        #for source_config in job_config.sources:
        #    source_restore_cmd = prepareSourceRestoreCommand(source_config, job_config, rclone_config)
        #    print(" ".join(source_restore_cmd))
        #    continue

        index = 1
        is_single_source = len(job_config.sources) < 2
        for source_config in job_config.sources:
            source_backup_cmd = prepareSourceBackupCommand(is_single_source, index, source_config, job_config, rclone_config)
            #print(source_backup_cmd)
            #continue
            result = subprocess.run(source_backup_cmd, env=cmd_env, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
                end = time.time()
                duration = datetime.timedelta(seconds=round(end - start))
                logError("Backup sync failed after {}".format(duration))
                logError(result.stdout)
                exit(1)

            index += 1

        fcntl.flock(lock_file_fd, fcntl.LOCK_UN)

        end = time.time()
        duration = datetime.timedelta(seconds=round(end - start))
        logInfo("Backup sync finished after {}".format(duration))
    except IOError:
        logInfo("Sync already running")
