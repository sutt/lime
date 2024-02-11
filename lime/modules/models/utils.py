import os
import sys
import yaml
import json
import pkg_resources

CONFIG_DIR = '.lime'
CONFIG_FN = 'config.yaml'
# TODO - rename this
CONFIG_DIR_NAME = os.path.join(CONFIG_DIR, CONFIG_FN)

def get_usr_config_dir():
    '''
        look for .lime in home dir
    '''
    try:
        home = os.path.expanduser('~')
        if os.path.exists(os.path.join(home, CONFIG_DIR_NAME)):
            return os.path.join(home, CONFIG_DIR_NAME)
    except Exception as e:
        return None

def get_workspace_config_dir():
    '''
        walk backwards to root trying to find .lime dir
        the first example you find is the one you use
    '''
    try:
        cwd = os.getcwd()
        while cwd != os.path.expanduser('~'):
            if os.path.exists(os.path.join(cwd, CONFIG_DIR_NAME)):
                return os.path.join(cwd, CONFIG_DIR_NAME)
            cwd = os.path.dirname(cwd)
    except Exception as e:
        return None
    return None

def get_lime_version():
    try:
        return pkg_resources.get_distribution('lime').version
    except Exception as e:
        return 'unknown'