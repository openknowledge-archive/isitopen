"""Pylons environment configuration"""
import os

import pylons
from pylons import config

import isitopen.lib.app_globals as app_globals
import isitopen.lib.helpers
from isitopen.config.routing import make_map
from pylons.i18n.translation import ugettext
from genshi.template import TemplateLoader
from genshi.filters.i18n import Translator

from sqlalchemy import engine_from_config

def load_environment(global_conf, app_conf):
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
    config.init_app(global_conf, app_conf, package='isitopen',
                    template_engine='genshi', paths=paths)

    config['routes.map'] = make_map()
    config['pylons.g'] = app_globals.Globals()
    config['pylons.h'] = isitopen.lib.helpers

    # Customize templating options via this variable
    tmpl_options = config['buffet.template_options']

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)

    engine = engine_from_config(config, 'sqlalchemy.')
    config['pylons.g'].sa_engine = engine
    
    # Translator (i18n)
    translator = Translator(ugettext)
    def template_loaded(template):
        template.filters.insert(0, translator)
        #translator.setup(template)
    
    
    # redo template setup to use genshi.search_path
    # This requires path notation in calls to render rather than dotted notation
    # e.g. render('index.html') not render('index') etc
    genshi = config['buffet.template_engines'].pop()
    # set None for template_root as not using dotted (python package) notation
    config.add_template_engine('genshi', None)
    tmpl_options = config['buffet.template_options']
    tmpl_options['genshi.search_path'] = paths['templates'][0]
    tmpl_options["genshi.loader_callback"] = template_loaded
    
