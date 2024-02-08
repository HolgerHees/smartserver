#!/usr/bin/python

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.plugins.action import ActionBase
from ansible.template import Templar

from ansible.module_utils.common.text.converters import to_text

import re

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):

        config_file = self._task.args.get('file')
        custom_var_keys = self._task.args.get('custom_var_keys')
        vault_var_keys = self._task.args.get('vault_var_keys')

        result = super(ActionModule, self).run(task_vars=task_vars)

        b_data, show_content = self._loader._get_file_contents(config_file)
        data = to_text(b_data, errors='surrogate_or_strict')

        config_data = self._loader.load(data, file_name=config_file, show_content=show_content)

        missing_vars = {} # contains error data from template parsing
        other_errors = [] # contains error data from template parsing

        requirement_checks = {} # variables with requirement attribute
        post_checks = {} # variables with dependency or optional attributes
        parser_result = {}
        result['ansible_facts'] = {}

        # process default var configs
        for var_name, var_value in config_data.items():
            if var_name == "default_variables":
                for default_var_name, default_var_value in var_value.items():
                    # remove known variables to get a list of custom variables
                    if default_var_name in custom_var_keys:
                        custom_var_keys.remove(default_var_name)

                    # remove known variables to get a list of vault variables
                    if default_var_name in vault_var_keys:
                        vault_var_keys.remove(default_var_name)

                    # remember requirement to check at the end
                    if "requirement" in default_var_value:
                        requirement_checks[default_var_name] = default_var_value

                    # variable with a dependency is processed later, after default variables are applied
                    if "dependency" in default_var_value:
                        post_checks[default_var_name] = default_var_value
                        continue

                    # optional variable is processed later, after default variables are applied
                    if "optional" in default_var_value:
                        post_checks[default_var_name] = default_var_value
                        continue

                    # adjusted variables (without optional and dependeny) already defined in task_vars and don't need to process
                    if default_var_name in task_vars:
                        parser_result[default_var_name] = {"name": default_var_name, "state": "adjusted"}
                        continue

                    # default variables (without optional and dependeny) can be assigned to task_vars
                    if "default" in default_var_value:
                        parser_result[default_var_name] = {"name": default_var_name, "state": "default"}
                        result['ansible_facts'][default_var_name] = task_vars[default_var_name] = default_var_value["default"]
                        continue

                    # missing variables
                    parser_result[default_var_name] = {"name": default_var_name, "state": "missing"}
            else:
                result['ansible_facts'][var_name] = task_vars[var_name] = config_data[var_name]

        # render all template variables (applied defaults and already defined variables)
        for var_name, var_value in result['ansible_facts'].items():
            result['ansible_facts'][var_name] = task_vars[var_name] = self.render(var_name, var_value, var_value, missing_vars, other_errors)
            #self._display.v('Test "%s" "%s"' % (var_name, result['ansible_facts'][var_name]))

        # process dependency_checks (check if a variable is used or not)
        for default_var_name, default_var_value in post_checks.items():
            if "dependency" in default_var_value:
                is_allowed = self.render(default_var_name, default_var_value["dependency"], False, missing_vars, other_errors)
                if not is_allowed:
                    if default_var_name in task_vars:
                        # variables that are defined, but not needed
                        parser_result[default_var_name] = {"name": default_var_name, "state": "unneeded"}
                    else:
                        # variables that are not defined, but also not needed => unused
                        parser_result[default_var_name] = {"name": default_var_name, "state": "unused"}
                    continue

            # adjusted variables already defined in task_vars
            if default_var_name in task_vars:
                parser_result[default_var_name] = {"name": default_var_name, "state": "adjusted"}
                continue

            if "optional" in default_var_value:
                is_optional = self.render(default_var_name, default_var_value["optional"], False, missing_vars, other_errors)
                # optional variables, which are not defined are unused
                if is_optional:
                    parser_result[default_var_name] = {"name": default_var_name, "state": "unused"}
                    continue

            # mandatory variable with a default value
            if "default" in default_var_value:
                #if default_var_name in ["weather_api_provider","weather_mqtt_publish_topic","weather_api_username","weather_api_password"]:
                #    self._display.v('Test "%s"' % (default_var_name))
                parser_result[default_var_name] = {"name": default_var_name, "state": "default"}
                result['ansible_facts'][default_var_name] = task_vars[default_var_name] = self.render(default_var_name, default_var_value["default"], default_var_value["default"], missing_vars, other_errors)
                continue

            # missing mandatory variable
            parser_result[default_var_name] = {"name": default_var_name, "state": "missing"}

        # validate that all variables are processed
        #for default_var_name in config_data["default_variables"].keys():
        #    if default_var_name not in parser_result:
        #        self._display.v('MISSING DEFAULT VAR HANDLING "%s"' % (default_var_name))
        #    if default_var_name in task_vars:
        #        self._display.v('VAR "%s" "%s" "%s"' % (default_var_name, type(task_vars[default_var_name]), task_vars[default_var_name]))

        # process requirement_checks
        missing_requirements = {}
        for default_var_name, default_var_value in requirement_checks.items():
            requirements = self.render(default_var_name, default_var_value["requirement"], False, missing_vars, other_errors)
            # somthing went wrong during rendering, error should be registered
            if not requirements:
                continue

            requirement_var_names = requirements.split(',')

            for requirement_var_name in requirement_var_names:
                # dependency does not exists
                if requirement_var_name not in task_vars:
                    other_errors.append("Requirement '{}', used in '{}' does not exists".format(requirement_var_name, default_var_name))
                    continue

                # dependency is satisfied
                if task_vars[requirement_var_name]:
                    continue

                if requirement_var_name not in missing_requirements:
                    missing_requirements[default_var_name] = []

                missing_requirements[default_var_name].append(requirement_var_name)

        # process unknown variables as custom vars
        for additional_custom_var_key in custom_var_keys:
            parser_result[additional_custom_var_key] = {"name": additional_custom_var_key, "state": "custom"}
        for additional_vault_var_key in vault_var_keys:
            parser_result[additional_vault_var_key] = {"name": additional_vault_var_key, "state": "vault"}

        # process errors
        error_messages = []
        for missing_var_name in list(missing_vars.keys()):
            # missing variable is already mentioned as failed
            if missing_var_name in parser_result and parser_result[missing_var_name]["state"] == "missing":
                del missing_vars[missing_var_name]
            else:
                # other variables, using this variable should be resettet to 'unknown'
                for used_in_var_name in missing_vars[missing_var_name]:
                    if used_in_var_name in parser_result:
                        parser_result[used_in_var_name]["state"] = "unknown"
        for missing_var_name, missing_var_value in missing_vars.items():
            error_messages.append(u"Variable '{}' used in ['{}'] is missing".format(missing_var_name, "','".join(missing_var_value)))

        error_messages += list(set(other_errors))

        # prepare result
        parser_result_values = list(parser_result.values())
        parser_result_values.sort(key=lambda variable: variable["name"])

        result['ansible_facts'].update( { "parser_custom_variables": [], "parser_vault_variables": [], "parser_adjusted_variables": [], "parser_default_variables": [], "parser_unneeded_variables": [], "parser_unused_variables": [], "parser_missing_variables": [],  "parser_unknown_variables": [] } )
        for parser_result_value in parser_result_values:
            result['ansible_facts']["parser_{}_variables".format(parser_result_value["state"])].append(parser_result_value["name"])

        result['ansible_facts']["parser_missing_requirements"] = missing_requirements
        result['ansible_facts']["parser_all_variables"] = parser_result_values
        result['ansible_facts']["parser_errors"] = error_messages

        self._display.v('Config test %s' % (error_messages))

        #if result.get('skipped', False):
        #    return result

        return result

    def render(self, var_name, var_value, fallback_value, missing_vars, other_errors):
        try:
            return self._templar.template(var_value)
        except AnsibleUndefinedVariable as e:
            match = re.search(r'\'([^\']+)\' is undefined', str(e))
            if( match ):
                missing_var_name = match.group(1)
                if missing_var_name not in missing_vars:
                    missing_vars[missing_var_name] = []
                missing_vars[missing_var_name].append(var_name)
            else:
                other_errors.append(str(e))
        except AnsibleError as e:
            other_errors.append(str(e))

        return fallback_value

