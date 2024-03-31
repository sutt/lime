import os, sys, json, pytest
import importlib
from unittest.mock import patch
from openai.types.chat import ChatCompletion
sys.path.append('.')
from lime.commands.eval import eval_sheet
from lime.common.controllers.parse import parse_to_obj
from lime.common.inference.api_openai import OpenAIModelObj


'''
    Load different configs / input_sheets and run eval_sheet.
    Focus on setting and overiding on gen_params + profile_params.

    Test Strategy:
    - build sheet_obj
    - stub config
        - construct infer_obj (in context)
    - stub openai api call
        - eval_sheet(sheet_obj, infer_obj) (in context)
        - capture kwargs of api call
    - assert on output and api call kwargs
'''

# utils and settings for tests
patch_path_usr = 'lime.common.models.utils.get_usr_config_dir'
patch_path_ws  = 'lime.common.models.utils.get_workspace_config_dir'
patch_ret_ws   = './tests/data/model_cfg/config-1.yaml'
completion_fn = './tests/data/stubs/completion.json'

def reset_imports():
    '''
        needed before each call to construct the infer_obj
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
def test_eval_1a():
    '''
        sheet = mix-params
        config = none
    '''
    
    # read in mix-params where there's a mix of sheet-level 
    # and question-level params
    sheet_obj = parse_to_obj(
         './tests/data/model_cfg/input-mix-params.md', 
         './lime/data/md-schema.yaml',
    )

    # patch the imports to no usr or ws config
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=None)
        ):
        
        reset_imports()
        
        infer_obj = OpenAIModelObj('gpt-3.5-turbo')

    # setup the patch on openai api call
    # write the kwargs of to captured_params
    captured_params = []
    mock_response = ChatCompletion(**json.load(open(completion_fn, 'r')))
    def mock_create(*args, **kwargs):
        captured_params.append(kwargs)
        return mock_response

    p_method = 'openai.resources.chat.completions.Completions.create'
    with patch(p_method) as mock_completions_create:
    
        mock_completions_create.side_effect = (
             lambda *args, **kwargs: mock_create(*args, **kwargs)
        )

        output = eval_sheet(
            sheet_obj,
            infer_obj,
            run_id='aaff'
        )

        assert mock_completions_create.call_count == 2
        
    assert len(output.questions) == 2
    
    assert output.questions[0].completion == "\"Grazie per i muffin alla griglia.\""

    assert captured_params[0].get('seed') is None       # not set on first question
    assert captured_params[0].get('max_tokens') == 29   # set at sheet level
    assert captured_params[1].get('seed') == 999        # set at question level
    assert captured_params[1].get('max_tokens') == 1    # set at sheet level


def test_eval_1b():
    '''
        sheet = mix-params
        config = config-1
    '''
    
    # read in mix-params where there's a mix of sheet-level 
    # and question-level params
    sheet_obj = parse_to_obj(
         './tests/data/model_cfg/input-mix-params.md', 
         './lime/data/md-schema.yaml',
    )

    # patch the imports to no usr or ws config
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=patch_ret_ws)
        ):
        
        reset_imports()
        
        infer_obj = OpenAIModelObj('gpt-3.5-turbo')

    # loaded in config, overidden later
    infer_obj.gen_params['max_tokens'] == 33

    # setup the patch on openai api call
    # write the kwargs of to captured_params
    captured_params = []
    mock_response = ChatCompletion(**json.load(open(completion_fn, 'r')))
    def mock_create(*args, **kwargs):
        captured_params.append(kwargs)
        return mock_response

    p_method = 'openai.resources.chat.completions.Completions.create'
    with patch(p_method) as mock_completions_create:
    
        mock_completions_create.side_effect = (
             lambda *args, **kwargs: mock_create(*args, **kwargs)
        )

        output = eval_sheet(
            sheet_obj,
            infer_obj,
            run_id='aaff'
        )

    assert captured_params[0].get('seed') == 1          # set in config
    assert captured_params[0].get('max_tokens') == 29   # set at sheet level
    assert captured_params[1].get('seed') == 999        # set at question level
    assert captured_params[1].get('max_tokens') == 1    # set at sheet level

def test_eval_2a():
    '''
        sheet = sheet-params
        config = config-1
    '''
    
    # read in mix-params where there's a mix of sheet-level 
    # and question-level params
    sheet_obj = parse_to_obj(
         './tests/data/model_cfg/input-sheet-params.md', 
         './lime/data/md-schema.yaml',
    )

    # patch the imports to no usr or ws config
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=patch_ret_ws)
        ):
        
        reset_imports()
        
        infer_obj = OpenAIModelObj('gpt-3.5-turbo')

    # loaded in config, overidden later
    infer_obj.gen_params['max_tokens'] == 33

    # setup the patch on openai api call
    # write the kwargs of to captured_params
    captured_params = []
    mock_response = ChatCompletion(**json.load(open(completion_fn, 'r')))
    def mock_create(*args, **kwargs):
        captured_params.append(kwargs)
        return mock_response

    p_method = 'openai.resources.chat.completions.Completions.create'
    with patch(p_method) as mock_completions_create:
    
        mock_completions_create.side_effect = (
             lambda *args, **kwargs: mock_create(*args, **kwargs)
        )

        output = eval_sheet(
            sheet_obj,
            infer_obj,
            run_id='aaff'
        )

    assert captured_params[0].get('seed') == 1          # set in config
    assert captured_params[0].get('max_tokens') == 55   # set in sheet
    assert captured_params[0].get('temperature') == 0.5 # set in sheet
    assert captured_params[1].get('seed') == 1          # set in config
    assert captured_params[1].get('max_tokens') == 55   # set in sheet
    assert captured_params[1].get('temperature') == 0.5 # set in sheet
    

def test_eval_2b():
    '''
        sheet = question-params
        config = config-1
    '''
    
    # read in mix-params where there's a mix of sheet-level 
    # and question-level params
    sheet_obj = parse_to_obj(
         './tests/data/model_cfg/input-question-params.md', 
         './lime/data/md-schema.yaml',
    )

    # patch the imports to no usr or ws config
    with (
            patch(patch_path_usr,   return_value=None),
            patch(patch_path_ws,    return_value=patch_ret_ws)
        ):
        
        reset_imports()
        
        infer_obj = OpenAIModelObj('gpt-3.5-turbo')

    # loaded in config, overidden later
    infer_obj.gen_params['max_tokens'] == 33
    infer_obj.gen_params['temperature'] == 0
    infer_obj.gen_params['seed'] == 1


    # setup the patch on openai api call
    # write the kwargs of to captured_params
    captured_params = []
    mock_response = ChatCompletion(**json.load(open(completion_fn, 'r')))
    def mock_create(*args, **kwargs):
        captured_params.append(kwargs)
        return mock_response

    p_method = 'openai.resources.chat.completions.Completions.create'
    with patch(p_method) as mock_completions_create:
    
        mock_completions_create.side_effect = (
             lambda *args, **kwargs: mock_create(*args, **kwargs)
        )

        output = eval_sheet(
            sheet_obj,
            infer_obj,
            run_id='aaff'
        )

    assert captured_params[0].get('seed') == 617        # set in question
    assert captured_params[0].get('max_tokens') == 33   # set in config
    assert captured_params[0].get('temperature') == 0.617 # set in question
    assert captured_params[1].get('seed') == 999        # set in question
    assert captured_params[1].get('max_tokens') == 999  # set in question
    assert captured_params[1].get('temperature') == 0 # set in config
    


