from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import default

from ansible.playbook.task_include import TaskInclude
from ansible import constants as C

import os

deployment_path = os.path.dirname(os.path.abspath(__file__)).rsplit('/',1)[0] + '/'

class CallbackModule(default.CallbackModule):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'default'

    '''def __init__(self):
        super(CallbackModule, self).__init__()'''

    def set_options(self, task_keys=None, var_options=None, direct=None):
        self._plugin_options = {
            'display_skipped_hosts': True,
            'display_ok_hosts': True,
            'display_failed_stderr': False,
            'show_custom_stats': False,
            'show_per_host_start': False,
            'check_mode_markers': False,
            'show_task_path_on_failure': False
        }

        # for backwards compat with plugins subclassing default, fallback to constants
        for option, value in self._plugin_options.items():
            setattr(self, option, value)

    def v2_playbook_on_include(self, included_file):
        self._display.display('included: [%s] => %s' % (", ".join([h.name for h in included_file._hosts]), included_file._filename.replace(deployment_path,"")))

    def v2_runner_on_skipped(self, result):
        if isinstance(result._task, TaskInclude):
            msg = "skipping: [%s] => %s" % ( result._host.get_name(), result._task.args['_raw_params'])
            self._display.display(msg, color=C.COLOR_SKIP)
        else:
            super(CallbackModule, self).v2_runner_on_skipped(result)
