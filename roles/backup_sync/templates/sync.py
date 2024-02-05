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

class VaildationException(Exception):
    pass

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
    args_cfg = { "job": None}
    args_values = ArgsParser.parse(args_cfg,sys.argv)

    if not args_values["job"]:
        return [None, "Please specify a job"]

    try:
        job_config = importlib.import_module("config.jobs.{}".format(args_values["job"]))
        return job_config
    except ModuleNotFoundError:
        raise VaildationException("Job '{}' not found".format(args_values["job"]))

def validateConfig(config, job_config):
    if job_config.rclone_config:
        remote_config = "{}rclone/{}".format(config.config_dir,job_config.rclone_config)
        if not os.path.exists(rclone_config):
            raise VaildationException("Missing config for remote '{}'. Check '{}'".format( job_config.rclone_remote, rclone_config))
        return remote_config
    return None

def prepareEnv(config, job_config):
    env = {"PATH": "/usr/bin/"}
    if job_config.password:
        result = subprocess.run([config.rclone_cmd, "obscure", job_config.password], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            raise VaildationException("Obscuration of password failed\n" + result.stdout)

        password = result.stdout.strip()

        env["RCLONE_CONFIG_BACKUP_TYPE"] = "crypt"
        env["RCLONE_CONFIG_BACKUP_FILENAME_ENCRYPTION"] = "standard"
        env["RCLONE_CONFIG_BACKUP_DIRECTORY_NAME_ENCRYPTION"] = "true"
        env["RCLONE_CONFIG_BACKUP_PASSWORD"] = password
    return env

def validateSourceAndDestination(config, job_config):
    with open("/etc/fstab") as f:
        fstab_data = f.read()
        path = job_config.destination
        while path != '/':
            #print(path)
            if path in fstab_data:
                logInfo("Check mountpoint '{}'".format(path))
                result = subprocess.run(["/usr/bin/mountpoint", path], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if result.returncode != 0:
                    raise VaildationException("Mountpoint '{}' not mounted".format(path))
                break
            path = os.path.dirname(path)

    for source in job_config.sources:
        if not os.path.exists(source["path"]):
            raise VaildationException("Source path '{}' does not exist".format(source["path"]))

def prepareCommand(is_single_source, index, source_config, job_config, remote_config):
    index_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not is_single_source:
        index_name = "{}_{}".format(source_config["name"] if source_config["name"] else "source{}".format(index), index_name)
    logfile = job_config.logfile.replace("[INDEX]", index_name)

    destination = job_config.destination
    if not destination.endswith(os.path.sep):
        destination += os.path.sep
    if source_config["name"]:
        destination += source_config["name"] + os.path.sep

    # rsync can be replaced completly if rclone has full metadata support
    if job_config.sync_type == 'rclone':
        # "--delete-excluded" should not be included, because of multi source support
        cmd = [config.rclone_cmd, "--links", "--log-level", "INFO", "--one-file-system"]
    else:
        # "--delete-excluded" should not be included, because of multi source support
        cmd = [config.rsync_cmd, "-avz", source_config["path"], destination, "--delete"]

    cmd.append("--log-file")
    cmd.append(logfile)

    if job_config.bandwidth_limit:
        cmd.append("--bwlimit")
        cmd.append(job_config.bandwidth_limit)

    if source_config["filter"]:
        for filter in source_config["filter"]:
            cmd.append("--filter")
            cmd.append(filter)

    if source_config["options"]:
        for option in source_config["options"]:
            cmd.append(option)

    if job_config.sync_type == 'rclone':
        if not remote_config:
            cmd.append("--metadata")

        if remote_config:
            cmd.append("--config=\"{}\"".format(remote_config))

        if job_config.password:
            cmd.append("--crypt-remote")
            cmd.append(destination)
            destination = "backup:"

        cmd.append("sync")
        cmd.append(source_config["path"])
        cmd.append(destination)

        cmd.append("--create-empty-src-dirs")

    return cmd

try:
    job_config = loadJobConfig()

    remote_config = validateConfig(config, job_config)

    cmd_env = prepareEnv(config, job_config)

    validateSourceAndDestination(config, job_config)
except VaildationException as e:
    logError(e)
    exit(1)

with open(job_config.lockfile, "w") as lock_file_fd:
    try:
        fcntl.flock(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError as e:
        logInfo("Sync already running")
        exit

    start = time.time()
    logInfo("Starting backup sync")

    index = 1
    is_single_source = len(job_config.sources) < 2
    for source_config in job_config.sources:
        cmd = prepareCommand(is_single_source, index, source_config, job_config, remote_config)
        #print(cmd)
        #continue

        result = subprocess.run(cmd, env=cmd_env, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
