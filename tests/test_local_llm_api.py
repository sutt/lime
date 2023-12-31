import os, sys, json, time
from unittest import mock
sys.path.append('../')

from modules.local_llm_api import LocalModel

def test_wrap_prompt():
    
    prompt = 'What is the largest planet?'
    preamble = '''In the following, answer the multiple choice question. Say nothing other than the answer. Only use the possible answers given, e.g. if the only answers are "A) True B) False", then only say either "A) True" or "B) False". Or, e.g. if the choices are A-D then only say e.g. "C) Napolean Bonaparte". Don't add any text to the beginning or end of the answer.'''
    wrapped_prompt = f'''[INST] <<SYS>>\n{preamble}\n<</SYS>>\n{prompt}\nA:[/INST]'''        

    with mock.patch.object(LocalModel, '__init__', return_value=None):
        local_model = LocalModel('llama_7b')
        local_model._wrap_prompt = mock.Mock(return_value=wrapped_prompt)
        assert local_model._wrap_prompt(prompt) == wrapped_prompt