import os, sys, json, time
from unittest import mock

from lime.common.inference.local_llama_cpp import (
    LocalModelObj,
    wrap_prompt,
)

def test_wrap_prompt():
    
    prompt = 'What is the largest planet?'
    preamble = '''In the following, answer the multiple choice question.'''
    WRAPPED_PROMPT = f'''<s>[INST]{preamble} {prompt} [/INST]'''        

    assert wrap_prompt(sys_prompt=preamble, usr_prompt=prompt) == WRAPPED_PROMPT
