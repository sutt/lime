import os, sys, json
from unittest import mock

from lime.commands.eval import (
    eval_sheet, 
)
from lime.common.controllers.parse import (
    parse_to_obj,
)
from lime.common.inference.base import (
    PromptModelResponse,
)
from lime.common.inference.api_openai import (
    OpenAIModelObj,
)
from openai.types.chat import ChatCompletion

# from lime.common.controllers.parse import parse_wrapper
# from lime.common.inference.local_cpp import get_model_fn

def load_chat_completion(fn: str) -> ChatCompletion:
    '''need this since oai_api.get_completion takes a ChatCompletion object'''
    with open(fn, 'r') as f:
        data = json.load(f)
        try:
            return ChatCompletion(**data)
        except Exception as e:
            print(e)
    
RESPONSE_STUB_FN = './tests/data/stubs/completion.json'
MODEL_RESPONSE_STUB = load_chat_completion(RESPONSE_STUB_FN)

def test_stub_loaded():
    '''test to make sure subsequent tests are valid'''
    model = OpenAIModelObj('gpt-3.5-turbo')
    msg = model._get_completion(MODEL_RESPONSE_STUB)
    assert len(msg) > 0

def test_get_model_fn():
    '''
        TODO - add mocks for workspace / usr config so we can get
                fn for a model name
    '''
    pass

def test_eval_basic_1():
    '''
        - demonstrate mocking submit_prompt
        - checks on the output object

    '''

    input_md = './tests/data/input-three.md'
    input_schema = './lime/data/md-schema.yaml'

    sheet_obj = parse_to_obj(input_md, input_schema)
    infer_obj = OpenAIModelObj('gpt-3.5-turbo')
    
    completion = infer_obj._get_completion(MODEL_RESPONSE_STUB)
    mock_return_value = PromptModelResponse(completion, None)
    
    with mock.patch('lime.common.inference.api_openai.OpenAIModelObj.prompt_model') as mock_submit_prompt:
            
        mock_submit_prompt.return_value = mock_return_value
            
        output = eval_sheet(
            sheet_obj,
            infer_obj,
            run_id='aaff'
        )

        # two questions thus it should be called twice
        assert mock_submit_prompt.call_count == 2
        assert len(output.questions) == 2

    # various header properties
    assert output.header.run_id == 'aaff'
    assert output.header.name_model == 'gpt-3.5-turbo'
    # not set inside this function, is set outside in the calling function eval:main
    assert output.header.sheet_fn is None 

    #  various questions level properties
    output.questions[0].name == 'Q1'
    eval_time = output.questions[0].eval_time
    assert isinstance(eval_time, float)
    # assert eval_time > 0.0
    STUB_COMPLETION = '"Grazie per i muffin alla griglia."'
    assert output.questions[0].completion == STUB_COMPLETION
    assert output.questions[1].completion == STUB_COMPLETION # same for both questions
    assert output.questions[0].error is None

    # assert output.questions[0].ntokens is None

    # note this derived separately and not attached to the stub
    STUB_NTOKENS = {
        "usr": 30,
        "sys": 17,
        "cmp": 11   # this is not certain, dont depend on it
    }
    ntokens = output.questions[0].ntokens
    ntokens = ntokens.model_dump()
    assert ntokens.get('usr') > 0 
    assert ntokens.get('sys') > 0

    # assert output.questions[0].ntokens.get('sys') == STUB_NTOKENS['sys']
    # assert output.questions[0].ntokens.get('usr') == STUB_NTOKENS['usr']


    