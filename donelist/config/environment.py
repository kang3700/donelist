"""Pylons environment configuration"""
import os

from pylons import config

import donelist.lib.app_globals as app_globals
import donelist.lib.helpers
from donelist.config.routing import make_map
import donelist.config as donelist_config
def load_environment(global_conf, app_conf, setup_globals=True):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='donelist',
                    template_engine='mako', paths=paths)

    g = config['pylons.g'] = app_globals.Globals(global_conf, app_conf, paths)
    if setup_globals:
        g.setup(global_conf)
        # donelist_config.cache = g.cache
    config['routes.map'] = make_map()
    config['pylons.h'] = donelist.lib.helpers
    config['pylons.response_options']['headers'] = {}
    # Customize templating options via this variable
    tmpl_options = config['buffet.template_options']
 
    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
