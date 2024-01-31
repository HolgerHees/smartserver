#!/usr/bin/python

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.plugins.action import ActionBase
from ansible.template import Templar

from ansible.module_utils.common.text.converters import to_text

import re

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):

        self.config_file = self._task.args.get('file')

        result = super(ActionModule, self).run(task_vars=task_vars)

        b_data, show_content = self._loader._get_file_contents(self.config_file)
        data = to_text(b_data, errors='surrogate_or_strict')

        config_data = self._loader.load(data, file_name=self.config_file, show_content=show_content)

        parser_result = {}
        optional_result = {}
        result['ansible_facts'] = {}

        # process default var configs
        for var_name, var_value in config_data.items():
            if var_name == "default_variables":
                for default_var_name, default_var_value in var_value.items():
                    if default_var_name in task_vars:
                        parser_result[default_var_name] = {"name": default_var_name, "state": "custom"}
                        continue

                    if "optional" in default_var_value:
                        optional_result[default_var_name] = {"name": default_var_name, "optional": default_var_value["optional"], "default": default_var_value["default"] if "default" in default_var_value else None }
                        parser_result[default_var_name] = {"name": default_var_name, "state": "optional"}
                        continue

                    if "default" in default_var_value:
                        result['ansible_facts'][default_var_name] = task_vars[default_var_name] = default_var_value["default"]
                        parser_result[default_var_name] = {"name": default_var_name, "state": "default"}
                        continue

                    parser_result[default_var_name] = {"name": default_var_name, "state": "missing"}
            else:
                result['ansible_facts'][var_name] = task_vars[var_name] = config_data[var_name]

        missing_vars = {}
        other_errors = []

        #templar = Templar(loader=None, variables=task_vars)
        for var_name, var_value in result['ansible_facts'].items():
            result['ansible_facts'][var_name] = task_vars[var_name] = self.render(var_name, var_value, var_value, missing_vars, other_errors)
            #self._display.v('Test "%s" "%s"' % (var_name, result['ansible_facts'][var_name]))

        for default_var_name, default_var_state in optional_result.items():
            is_optional = self.render(default_var_name, default_var_state["optional"], False, missing_vars, other_errors)
            if not is_optional:
                #if default_var_name == "vault_fritzbox_api_password":
                #    self._display.v('Test "%s"' % (is_optional))
                #    self._display.v('Test "%s"' % (task_vars["system_service_enabled"]))
                #    self._display.v('Test "%s"' % (task_vars["fritzbox_devices"]))
                #    self._display.v('Test "%s"' % (default_var_state["optional"]))
                #    self._display.v('Test "%s"' % (default_var_state["default"]))
                if default_var_state["default"] is not None:
                    result['ansible_facts'][default_var_name] = task_vars[default_var_name] = self.render(default_var_name, default_var_state["default"], default_var_state["default"], missing_vars, other_errors)
                    parser_result[default_var_name] = {"name": default_var_name, "state": "default"}
                else:
                    parser_result[default_var_name] = {"name": default_var_name, "state": "missing"}
            else:
                parser_result[default_var_name] = {"name": default_var_name, "state": "unneeded"}

        #for var_name, var_value in result['ansible_facts'].items():
        #    self._display.v('Test "%s" "%s"' % (var_name, type(var_value)))

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

        result['ansible_facts']["parser_errors"] = error_messages
        result['ansible_facts']["parser_missing_variables"] = list(map(lambda d: d['name'], list(filter( lambda item: item["state"] == "missing", parser_result_values))))
        result['ansible_facts']["parser_default_variables"] = list(map(lambda d: d['name'], list(filter( lambda item: item["state"] == "default", parser_result_values))))
        result['ansible_facts']["parser_custom_variables"] = list(map(lambda d: d['name'], list(filter( lambda item: item["state"] == "custom", parser_result_values))))
        result['ansible_facts']["parser_unneeded_variables"] = list(map(lambda d: d['name'], list(filter( lambda item: item["state"] == "unneeded", parser_result_values))))
        result['ansible_facts']["parser_all_variables"] = parser_result_values

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

