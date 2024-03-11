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

class ConfigException(Exception):
    pass

class JobException(Exception):
    pass

class LockException(Exception):
    pass

def logInfo(msg):
    if job_config is not None:
        print("{}: {}".format(job_config.name.upper(), msg), flush=True, file=sys.stdout)
    else:
        print(msg, flush=True, file=sys.stdout)
    #sys.stdout.flush()

def logError(msg):
    if job_config is not None:
        print("{}: {}".format(job_config.name.upper(), msg), flush=True, file=sys.stderr)
    else:
        print(msg, flush=True, file=sys.stderr)
    #sys.stderr.flush()

def loadJobConfig():
    args_cfg = { "job": None}
    args_values = ArgsParser.parse(args_cfg,sys.argv)

    if not args_values["job"]:
        return [None, "Please specify a job"]

    try:
        job_config = importlib.import_module("config.jobs.{}".format(args_values["job"]))
        return job_config
    except ModuleNotFoundError:
        raise ConfigException("Job '{}' not found".format(args_values["job"]))

def validateConfig(config, job_config):
    if job_config.rclone_config:
        remote_config = "{}rclone/{}".format(config.config_dir,job_config.rclone_config)
        if not os.path.exists(rclone_config):
            raise ConfigException("Missing config for remote '{}'. Check '{}'".format( job_config.rclone_remote, rclone_config))
        return remote_config
    return None

def prepareEnv(config, job_config):
    env = {"PATH": "/usr/bin/"}
    if job_config.password:
        result = subprocess.run([config.rclone_cmd, "obscure", job_config.password], encoding="utf-8", stdout=subprocess.PIPE, stderr=sys.stderr)
        if result.returncode != 0:
            raise ConfigException("Obscuration of password failed")

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
                result = subprocess.run(["/usr/bin/mountpoint", "-q", path ], encoding="utf-8", stdout=sys.stdout, stderr=sys.stderr)
                if result.returncode != 0:
                    raise ConfigException("Mountpoint '{}' not mounted".format(path))
                break
            path = os.path.dirname(path)

    for source in job_config.sources:
        if not os.path.exists(source["path"]):
            raise ConfigException("Source path '{}' does not exist".format(source["path"]))

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

    allowed_return_codes = [0]

    # rsync can be replaced completly if rclone has full metadata support
    if job_config.sync_type == 'rclone':
        # "--delete-excluded" should not be included, because of multi source support
        cmd = [config.rclone_cmd, "--links", "--metadata", "--one-file-system", "--log-level", "INFO", ]
    else:
        # "--delete-excluded" should not be included, because of multi source support
        cmd = [config.rsync_cmd, "-avz", source_config["path"], destination, "--one-file-system", "--delete", "--quiet"]

        if source_config["options"] and "--local-no-check-updated" in source_config["options"]:
            allowed_return_codes.append(24)
            source_config["options"].remove("--local-no-check-updated")

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

    return cmd, allowed_return_codes

try:
    job_config = loadJobConfig()

    remote_config = validateConfig(config, job_config)

    cmd_env = prepareEnv(config, job_config)

    validateSourceAndDestination(config, job_config)

    with open(job_config.lockfile, "w") as lock_file_fd:
        try:
            fcntl.flock(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            raise LockException("Sync already running")

        start = time.time()
        logInfo("Starting backup sync")

        index = 1
        is_single_source = len(job_config.sources) < 2
        for source_config in job_config.sources:
            cmd, allowed_return_codes = prepareCommand(is_single_source, index, source_config, job_config, remote_config)
            #print(allowed_return_codes)
            #print(cmd)
            #continue

            result = subprocess.run(cmd, env=cmd_env, encoding="utf-8", stdout=sys.stdout, stderr=sys.stderr)
            if result.returncode not in allowed_return_codes:
                fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
                raise JobException("Backup sync failed after {}".format(datetime.timedelta(seconds=round(time.time() - start))))

            index += 1

        fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
        logInfo("Backup sync finished after {}".format(datetime.timedelta(seconds=round(time.time() - start))))

except (ConfigException, JobException) as e:
    logError(e)
    exit(1)
except LockException as e:
    logInfo(e)

exit(0)

