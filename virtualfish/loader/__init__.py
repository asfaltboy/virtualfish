from __future__ import print_function
import os
import sys
import pkg_resources


def load(plugins=()):
    version = pkg_resources.get_distribution('virtualfish').version
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    commands = [
        'set -g VIRTUALFISH_VERSION {}'.format(version),
        'set -g VIRTUALFISH_PYTHON_EXEC {}'.format(sys.executable),
        '. {}'.format(os.path.join(base_path, 'virtual.fish')),
    ]

    for plugin in plugins:
        path = os.path.join(base_path, plugin + '.fish')
        if os.path.exists(path):
            commands.append('. {}'.format(path))
        else:
            raise ValueError("Plugin does not exist: " + plugin)

    commands.append('emit virtualfish_did_setup_plugins')
    return commands
