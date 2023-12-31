import os
import sys
import ctypes
from llama_cpp import (
    Llama, 
    llama_log_set, 
)

class LocalParams:
    max_tokens = 50
    temperature = 0.0


class LocalModelFns:
    llama_7b = '../../data/llama-2-7b.Q4_K_M.gguf'
    # llama_13b_chat = '../../data/llama-2-13b.Q4_K_M.gguf'


def get_model_fn(model_name: str) -> str:
    try:
        return getattr(LocalModelFns, model_name)
    except AttributeError:
        if os.path.isfile(model_name):
            return model_name
        else:
            raise ValueError(f'invalid model_name: {model_name}')
    except Exception as e:
        raise ValueError(f'exception in get_model_fn: {e}')
        

def wrap_prompt(prompt: str) -> str:
    # preamble = '''In the following, answer the multiple choice question. Say nothing other than tha answer. Answer the question using the letter of the choice, a right parenthesis, and the word(s) in the answer e.g. output "C) Napolean Bonaparte". Use commonsense and traditional folk wisdom where the question calls for it.'''
    preamble = '''In the following, answer the multiple choice question. Say nothing other than the answer. Only use the possible answers given, e.g. if the only answers are "A) True B) False", then only say either "A) True" or "B) False". Or, e.g. if the choices are A-D then only say e.g. "C) Napolean Bonaparte". Don't add any text to the beginning or end of the answer.'''
    print(prompt)
    return f'''[INST] <<SYS>>\n{preamble}\n<</SYS>>\n{prompt}\nA:[/INST]'''        


# suppress logs from printing to stdout
# there's still a little that leaks out
def my_log_callback(level, message, user_data): pass
log_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)(my_log_callback)
llama_log_set(log_callback, ctypes.c_void_p())


class LocalModel:
    def __init__(self, model_name='llama_7b'):
        self.init_params = {
            'n_threads': 4,
        }
        self.generate_params = {
            'temperature': LocalParams.temperature,
            'max_tokens': LocalParams.max_tokens,
        }
        self.llm = Llama(
            model_path=get_model_fn(model_name), 
            **self.init_params,
        )

    def __call__(self, prompt):
        output = self.llm(
            prompt=self._wrap_prompt(prompt), 
            **self.generate_params,
        )
        return output
    
    def _wrap_prompt(self, prompt):
        return wrap_prompt(prompt)
    
    @staticmethod
    def get_completion(output):
        return output['choices'][0]['text']
    
    @staticmethod
    def get_data(output):
        data = {
            'text': output['choices'][0]['text'],
            'completion_tokens': output['usage']['completion_tokens'],
        }
        return data


if __name__ == '__main__':
    
    print("start...\n")
    local_model = LocalModel('llama_7b')
    prompt = 'Q: What is the largest planet? A: '
    output = local_model(prompt)
    print(output)
    text = LocalModel.get_completion(output)
    print(text)
    print("\nend.")

