#!/usr/bin/python

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.plugins.action import ActionBase
from ansible.template import Templar

from ansible.module_utils.common.text.converters import to_text
from ansible.utils.version import SemanticVersion

import re
import subprocess

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        ansible_required_version = self._task.args.get('ansible_required_version')
        ansible_core_required_version = self._task.args.get('ansible_core_required_version')
        collection_versions_cmd = self._task.args.get('collection_versions_cmd')
        requirements_filename = self._task.args.get('requirements')

        result = super(ActionModule, self).run(task_vars=task_vars)
        result['_ansible_verbose_always'] = True

        requirementes_found = []
        requirementes_missing = []
        requirementes_hints = []

        _required_version = SemanticVersion(ansible_core_required_version)
        _installed_version = SemanticVersion(task_vars["ansible_version"]["full"])

        if _required_version <= _installed_version:
            requirementes_found.append("Required version '{}' of 'ansible' is installed".format(_installed_version.vstring))
        else:
            requirementes_missing.append("Reuired version '{}' of 'ansible-core' is missing".format(_required_version.vstring))
            requirementes_hints.append("Run 'pip install ansible=={}' to install version '{}' of 'ansible' which includes the required 'ansible-core' version '{}'".format(ansible_required_version, ansible_required_version, ansible_core_required_version))

        collection_versions = subprocess.run(collection_versions_cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8').split("\n")

        b_data, show_content = self._loader._get_file_contents(requirements_filename)
        data = to_text(b_data, errors='surrogate_or_strict')

        config_data = self._loader.load(data, file_name=requirements_filename, show_content=show_content)

        missing_collections = False
        for requirement in config_data["collections"]:
            required_version = SemanticVersion(requirement['version'])
            installed_version = None
            condition_met = False

            for line in collection_versions:
                match = re.search("{}\s*([0-9\.]*)".format(requirement['name']), line)
                if not match:
                    continue

                _installed_version = SemanticVersion(match.group(1))

                if installed_version is None or installed_version < _installed_version:
                    installed_version = _installed_version

                if required_version <= installed_version:
                    condition_met = True

            if not condition_met:
                requirementes_missing.append("Required version '{}' of collection '{}' is missing".format(required_version.vstring, requirement['name']))
                missing_collections = True
            else:
                requirementes_found.append("Required version '{}' of collection '{}' is installed".format(installed_version.vstring, requirement['name']))

        if missing_collections:
            requirementes_hints.append("Run 'ansible-galaxy install -r ./requirements.yml' to install missing collection requirements")

        if len(requirementes_missing) > 0:
            result['failed'] = True
            result["msg"] = requirementes_missing
            result["hint"] = requirementes_hints
        else:
            result["msg"] = requirementes_found

        return result
