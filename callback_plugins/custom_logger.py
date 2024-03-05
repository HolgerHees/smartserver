from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule
from ansible.playbook.task_include import TaskInclude


class CallbackModule(DefaultCallbackModule):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'default'

    def __init__(self):
        super(CallbackModule, self).__init__()

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

    #def v2_playbook_on_task_start(self, task, is_conditional):
    #    #if isinstance(task, TaskInclude):
    #    #    return

    #    self._display.v(">>>>>>>>>>>>>>>>>>>>>>>>>>")
    #    self._display.v(str(task.__class__))
    #    super(CallbackModule, self).v2_playbook_on_task_start(task, is_conditional)
    #    self._display.v("<<<<<<<<<<<<<<<<<<<<<<<<<<")

    def v2_playbook_on_include(self, included_file):
        pass
