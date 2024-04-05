import os, sys, json
from unittest import mock
from contextlib import contextmanager
from openai.types.chat import ChatCompletion
from lime.commands.eval import (
    eval_sheet, 
    batch_eval,
    get_sheet_fns,
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


def test_eval_basic_1():
    '''
        - demonstrate mocking submit_prompt
        - checks on the output object
        - infer_obj = OpenAIModelObj
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
    assert output.header.sheet_fn == 'input-three.md'

    #  various questions level properties
    output.questions[0].name == 'Q1'
    eval_time = output.questions[0].eval_time
    assert isinstance(eval_time, float)
    # assert eval_time > 0.0
    STUB_COMPLETION = '"Grazie per i muffin alla griglia."'
    assert output.questions[0].completion == STUB_COMPLETION
    assert output.questions[1].completion == STUB_COMPLETION # same for both questions
    assert output.questions[0].error is None

    # basic check on ntokens
    ntokens = output.questions[0].ntokens
    ntokens = ntokens.model_dump()
    assert ntokens.get('usr') > 0 
    assert ntokens.get('sys') > 0

    # note this derived separately and not attached to the stub
    # STUB_NTOKENS = {
    #     "usr": 30,
    #     "sys": 17,
    #     "cmp": 11   # this is not certain, dont depend on it
    # }
    # assert output.questions[0].ntokens.get('sys') == STUB_NTOKENS['sys']
    # assert output.questions[0].ntokens.get('usr') == STUB_NTOKENS['usr']


@contextmanager
def change_dir(target_directory):
    """Context manager for changing the current working directory."""
    original_directory = os.getcwd()
    os.chdir(target_directory)
    try:
        yield
    finally:
        os.chdir(original_directory)

def test_get_sheet_fns_1():

    data_dir = './tests/data/dir-three/a'
    
    input_paths = ['.']
    ANSWER = ['input-common-sense-1.md', 'input-common-sense-2.md', 'input-xx-a.md', 'input-xx-b.md', 'input-yy-a.md', 'input-yy-b.md']
    with change_dir(data_dir):
        sheet_fns = get_sheet_fns(input_paths)
    assert len(sheet_fns) == len(ANSWER)
    for fn in ANSWER:
        assert fn in sheet_fns

    input_paths = ['input-xx-a.md']
    ANSWER = ['input-xx-a.md']
    with change_dir(data_dir):
        sheet_fns = get_sheet_fns(input_paths)
    assert len(sheet_fns) == len(ANSWER)
    for fn in ANSWER:
        assert fn in sheet_fns

    input_paths = ['apple.md']
    ANSWER = ['apple.md']
    with change_dir(data_dir):
        sheet_fns = get_sheet_fns(input_paths)
    assert len(sheet_fns) == len(ANSWER)
    for fn in ANSWER:
        assert fn in sheet_fns

    input_paths = ['*xx*']
    ANSWER = ['input-xx-a.md', 'input-xx-b.md']
    with change_dir(data_dir):
        sheet_fns = get_sheet_fns(input_paths)
    assert len(sheet_fns) == len(ANSWER)
    for fn in ANSWER:
        assert fn in sheet_fns

    input_paths = ['xx*']
    ANSWER = None
    with change_dir(data_dir):
        try:
            sheet_fns = get_sheet_fns(input_paths)
            assert False, 'expected error not raised'
        except Exception as e:
            assert "No input files found in: ['xx*']" in str(e), 'expected error message not found'

    input_paths = ['*xx*', '*yy*']
    ANSWER = ['input-xx-a.md', 'input-xx-b.md', 'input-yy-a.md', 'input-yy-b.md']
    with change_dir(data_dir):
        sheet_fns = get_sheet_fns(input_paths)
    assert len(sheet_fns) == len(ANSWER)
    for fn in ANSWER:
        assert fn in sheet_fns
        
    input_paths = ['*xx*', 'apple.md']
    ANSWER = ['input-xx-a.md', 'input-xx-b.md', 'apple.md']
    with change_dir(data_dir):
        sheet_fns = get_sheet_fns(input_paths)
    assert len(sheet_fns) == len(ANSWER)
    for fn in ANSWER:
        assert fn in sheet_fns

    input_paths = ['*xx*', 'sdhsgjdgsjd.md']
    ANSWER = ['input-xx-a.md', 'input-xx-b.md']
    with change_dir(data_dir):
        sheet_fns = get_sheet_fns(input_paths)
    assert len(sheet_fns) == len(ANSWER)
    for fn in ANSWER:
        assert fn in sheet_fns

        
if __name__ == '__main__':
    test_get_sheet_fns_1()
    print('done')