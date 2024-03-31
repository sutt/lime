import os, sys, json, pytest
import importlib
from unittest.mock import patch
sys.path.append('.')

'''
    Test if params set from a variety of sources are correctly
    brought into the model object, or model object variants.

    This includes: loading, parsing, overriding, renaming the 
    parameters meant for generation action.

'''

# utils and settings for tests
patch_path_usr = 'lime.common.models.utils.get_usr_config_dir'
patch_path_ws  = 'lime.common.models.utils.get_workspace_config_dir'
patch_ret_ws   = './tests/data/model_cfg/'

def reset_imports():
    '''
        Needed before each call to construct the infer_obj
        this allows the new config stub to propagate to the 
        infer_obj instead of using value attained from first
        import.
    '''
    modules = [
        'lime.common.models.config',
        'lime.common.models.state',
        'lime.common.inference.base',
    ]
    for m in modules:
        importlib.reload(sys.modules[m])

# tests
def test_modelobj_1a():
    ''' loading no workspace config'''
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=None)
        ):
            from lime.common.inference.base import ModelObj
            reset_imports()
            infer_obj = ModelObj('')
            params = infer_obj.get_gen_params()
            assert params.get('max_tokens') == 100
            assert params.get('temperature') == 0
            assert params.get('seed') is None

def test_modelobj_1b():
    ''' loading from workspace config 1'''
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=patch_ret_ws + 'config-1.yaml')
        ):
            from lime.common.inference.base import ModelObj
            reset_imports()
            infer_obj = ModelObj('')
            params = infer_obj.get_gen_params()
            assert params.get('max_tokens') == 33
            assert params.get('temperature') == 0
            assert params.get('seed') == 1


def test_modelobj_1c():
    ''' loading from workspace config 2'''
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=patch_ret_ws + 'config-2.yaml')
        ):
            from lime.common.inference.base import ModelObj
            reset_imports()
            infer_obj = ModelObj('')
            params = infer_obj.get_gen_params()
            assert params.get('max_tokens') == 44
            assert params.get('temperature') == 0
            assert params.get('seed') == 2

def test_modelobj_2a():
    ''' loading from workspace config 3, call custom model'''
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=patch_ret_ws + 'config-3.yaml')
        ):
            from lime.common.inference.base import ModelObj
            reset_imports()
            infer_obj = ModelObj('gpt_3')  # this is in LocalModels
            params = infer_obj.get_gen_params()
            assert params.get('max_tokens') == 63   # set as config's profile param
            assert params.get('temperature') == 0   # remains as default
            assert params.get('seed') == 2          # set in config's LocalParams



if __name__ == '__main__':
    '''
    This section can help understand reset_imports rationale
    and how it can be used to debug side-effects.
    If you remove the reset_imports() call in the test functions, and run it
    you'll see that the first test will pass (1b), but the second (1c) will fail.
    This is because the first test sets the config to config-1, and the second test
    even after re-importing the ModelObj doesn't reset it's imports of other modules,
    like config, state, etc. So the second test will use the config-1 values instead.
    This can also be seen by running the below where _1c will fail after running _1b.
    To solidify this hypothesis, comment out running _1b in this section and _1c will pass.
    '''
    test_modelobj_1b()   
    test_modelobj_1c()
