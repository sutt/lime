import os
import io
import ctypes
from contextlib import redirect_stderr
from typing import (
    Dict,
)
from ..models.state import (
    ConfigLoader,
)
try:
    from llama_cpp import (
        Llama, 
        LlamaState,
        llama_log_set, 
    )
    llama_cpp_loaded = True
except ImportError:
    llama_cpp_loaded = False


llama_log_obj = []

class LocalParams(ConfigLoader):
    max_tokens = 50
    temperature = 0.0

LocalParams._initialize()


class LocalModelFns(ConfigLoader):
    _urn = {
        'data': lambda config: config.get('LocalModels'),
        'value': lambda data, key: data.get(key, {}).get('fn'),
    }
    llama_7b = None
    mistral_hf_7b = None

LocalModelFns._initialize()


class CppInference:
    def _get_package_version(package_name: str) -> str:
        try: return __import__(package_name).__version__
        except: return 'unable to get version'
    default_package = 'llama_cpp'
    package_version = _get_package_version(default_package)


class ChatTemplate:
    template = '''{{{SYS}}}{{{USR}}}'''
    default_templating_tag_left =  '''{{{'''
    default_templating_tag_right = '''}}}'''
    default_sys_tag = 'SYS'
    default_usr_tag = 'USR'
    left = None
    right = None
    
    @classmethod
    def wrap_prompt(
            cls,
            prompt: str = None,
            sys_prompt: str = None,
            usr_prompt: str = None,
        ) -> str: 
        pass


class DefaultModelChatTemplates:
    llama_7b = {
        
    }
    mistral_hf_7b = {
        'full': '',
        'left': '',
        'right': '',
    }


def suppress_stderr(func):
    def wrapper(*args, **kwargs):
        capture_stderr = io.StringIO()
        with redirect_stderr(capture_stderr):
            result = func(*args, **kwargs)
            llama_log_obj.append(capture_stderr.getvalue())
        return result
    return wrapper

def my_log_callback(level, message, user_data):
    llama_log_obj.append(message.decode())

log_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, 
            ctypes.c_char_p, ctypes.c_void_p)(my_log_callback)

def get_model_fn(model_name: str) -> str:
    try:
        model_fn = getattr(LocalModelFns, model_name)
        if not os.path.isfile(model_fn):
            raise ValueError(f'{model_name} is found in LocalModels but path: {model_fn} is not a file')
        return model_fn
    except AttributeError:
        if os.path.isfile(model_name):
            return model_name
        else:
            msg = f'model_name {model_name} is not a valid file'
            msg += f'or list of LocalModelFns: {", ".join(list(LocalModelFns._get_attrs().keys()))}'
            raise ValueError(msg)
    except Exception as e:
        raise ValueError(f'exception in get_model_fn: {e}')
        
def wrap_prompt(
        prompt: str = None,
        sys_prompt: str = None,
        usr_prompt: str = None,
    ) -> str:
    if prompt is not None:
        return f'''<s>[INST]{prompt} [/INST]'''
    if sys_prompt is not None and usr_prompt is not None:
        return f'''<s>[INST]{sys_prompt} {usr_prompt} [/INST]'''
    if sys_prompt is not None:
        return f'''<s>[INST]{sys_prompt} '''
    if usr_prompt is not None:
        return f'''{usr_prompt} [/INST]'''
    
def rename_llama_args(args: Dict) -> Dict:
    '''
        rename args to llama args
    '''
    arg_names = {
        'temperature': 'temp',
    }
    new_args = {}
    for k, v in args.items():
        if k in arg_names:
            new_args[arg_names[k]] = v
        else:
            new_args[k] = v
    return new_args


class LocalModel:
    '''
        use python_llama_cpp for inference
    '''
    
    @suppress_stderr
    def __init__(self, model_name: str, **params):
        
        self.init_params = {
            'n_threads': 4,
            'n_ctx': 512,
        }
        
        init_params = {**self.init_params, **params}
        
        self.generate_params = {
            'temperature': LocalParams.temperature,
            'max_tokens': LocalParams.max_tokens,
        }
        
        llama_log_set(log_callback, ctypes.c_void_p())
        
        self.llm : Llama = Llama(
            model_path=get_model_fn(model_name), 
            **init_params
        )

        self.cached_state : LlamaState = None

    def __call__(self, prompt, **params):
        wrapped_prompt = wrap_prompt(prompt)
        call_params = {**self.generate_params, **params}
        output = self.llm(
            prompt=wrapped_prompt, 
            **call_params,
        )
        return output
    
    def eval_prompt(self, prompt):
        # we're expecting this is a sys_prompt and thus
        # only wrap the left side. The usr_prompt will follow
        # and only be wrapped on the right side.
        wrapped_prompt = wrap_prompt(sys_prompt=prompt)
        tokenized_wrapped_prompt = self.llm.tokenize(wrapped_prompt.encode())
        self.llm.reset()
        self.llm.eval(tokenized_wrapped_prompt)  # **params_llm_eval

    def tokenize(self):
        pass
    
    @suppress_stderr
    def save_state(self):
        self.cached_state = self.llm.save_state()

    def load_state(self):
        self.llm.load_state(self.cached_state)
        
    def eval_question(
            self, 
            question_text: str, 
            seed: int = None, 
            max_tokens: int = LocalParams.max_tokens, 
            verbose: int = 0,
        ) -> Dict:
        # usr_prompt: only wrap right side
        wrapped_text = wrap_prompt(usr_prompt=question_text)
        tokens_question = self.llm.tokenize(wrapped_text.encode())
        self.llm.eval(tokens_question)
        if seed is not None: 
            self.llm.set_seed(seed) # Seed (if set) must be after eval
        counter = 0
        completion = ''
        token = self.llm.sample() # **params_llm_sample
        while token is not self.llm.token_eos() :
            if counter >= max_tokens: break
            counter += 1
            _token = self.llm.detokenize([token]).decode()
            completion += _token
            if verbose > 0:
                print(_token, end='', flush=True)
            self.llm.eval([token])
            token = self.llm.sample() # **params_llm_sample
        if verbose > 0: print(end='\n', flush=True)
        return {
            'text': completion,
            'completion_tokens': counter,
        }
    
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

class LocalModelCache:
    def __init__(self):
        self.model: LocalModel = None
        self.has_cache: bool = False
        self.sys_prompt_tokens: int = 0
    def get(self, model_name:str, sys_prompt:str):
        # TODO - re_init for larger context
        if self.model is None:
            self.model = LocalModel(model_name)
        if self.has_cache:
            self.model.load_state()
        else:
            self.model.eval_prompt(sys_prompt)
            self.model.save_state()
            self.has_cache = True
            self.sys_prompt = sys_prompt
    def eval_question(self, question_text:str, **params):
        # TODO - count tokens for n_ctx exapnsion
        # total_tokens = 0 # sys_prompt
        # total_tokens += params.get('max_tokens', 0)
        return self.model.eval_question(question_text, **params)
    def __call__(self, prompt: str):
        return self.model(prompt)
    

if __name__ == '__main__':
    
    print("start...\n")
    
    # local_model = LocalModel('llama_7b')
    # prompt = 'Q: What is the largest planet? A: '
    # output = local_model(prompt)
    # print(output)
    # text = LocalModel.get_completion(output)
    # print(text)
    # print("\nend.")

    # local_model = LocalModel('mistral_hf_7b')
    # prompt = 'Q: What is the largest planet? A: '
    # output = local_model(prompt)
    # print(output)
    # text = LocalModel.get_completion(output)
    # print(text)
    
    sys_prompt = '''
In the following answer only with the shortest amount words possible.
Only answer with the word(s) of the answer and don't include any other text.
Use your common sense and traditional folk wisdom where the question calls for it.
If there's not enough information to answer the question, then answer with "I don't know".
'''
    import time
    t0 = time.time()
    def mark():
        global t0
        print(f'{time.time()-t0:.2f}')
        t0 = time.time()

    # print(ConfigLoader.__loaded_configs)
    # print(list(LocalModelFns._get_attrs().items()))
    # print(list(LocalParams._get_attrs().items()))
    print(LocalParams._get_attrs())
    print(LocalModelFns._get_attrs())
    
    import sys
    sys.exit()

    cache = LocalModelCache()
    cache.get('mistral_hf_7b', sys_prompt)
    mark()
    
    usr_prompt = 'Q: What is the largest planet? A:'
    cache.get('mistral_hf_7b', sys_prompt)
    d = cache.eval_question(usr_prompt, seed=1)
    print(d.get('text'))
    mark()
    
    usr_prompt = 'Q: What is the smallest planet? A:'
    cache.get('mistral_hf_7b', sys_prompt)
    d = cache.eval_question(usr_prompt, seed=3)
    print(d.get('text'))
    mark()

    usr_prompt = 'Q: What is the mouse\'s name? A:'
    cache.get('mistral_hf_7b', sys_prompt)
    d = cache.eval_question(usr_prompt)
    print(d.get('text'))
    mark()
    

