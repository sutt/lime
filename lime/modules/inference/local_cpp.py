import os
import io
import ctypes
from contextlib import redirect_stderr
from typing import (
    Dict,
    Any,
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
    seed = None

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

def get_sample_args(args: Dict) -> Dict:
    arg_names = [
        'temperature',
        'top_k',
        'top_p',
    ]
    sample_args = {k: args[k] for k in args if k in arg_names}
    sample_args = rename_llama_args(sample_args)
    return sample_args


class LocalModel:
    '''
        use python_llama_cpp for inference
    '''

    def __init__(self, model_name:str=None, b_init:bool=True, **params):
        
        self.init_params = {
            'n_threads': 4,
            'n_ctx': 512,
        }
        self.init_params = {**self.init_params, **params}
        self.gen_params = {
            'temperature':  LocalParams.temperature,
            'max_tokens':   LocalParams.max_tokens,
            'seed':         LocalParams.seed,
        }
        self.llm : Llama = None
        self.cached_state : LlamaState = None
        self.b_init = False
        if b_init:
            self.init(model_name)
        
    @suppress_stderr
    def init(self, model_name: str):
        llama_log_set(log_callback, ctypes.c_void_p())
        self.llm = Llama(
            model_path=get_model_fn(model_name), 
            **self.init_params
        )
        self.b_init = True

    def set_gen_params(self, gen_params: Dict[str, Any]):
        self.gen_params = {**self.gen_params, **gen_params}

    def get_all_params(self):
        return {
            'init_params': self.init_params,
            'gen_params': self.gen_params,
            'pkg_version': {
                # k:v for k,v in CppInference.__dict__
                # if not k.startswith('_')
            },
        }

    def __call__(self, prompt):
        wrapped_prompt = wrap_prompt(prompt)
        output = self.llm(
            prompt=wrapped_prompt, 
            **self.gen_params,
        )
        return output
    
    def eval_prompt(self, prompt):
        wrapped_prompt = wrap_prompt(sys_prompt=prompt)
        tokenized_wrapped_prompt = self.llm.tokenize(wrapped_prompt.encode())
        self.llm.reset()
        self.llm.eval(tokenized_wrapped_prompt)

    def num_tokens(self, text: str) -> int:
        try:
            tokens = self.llm.tokenize(text.encode())
            return len(tokens)
        except:
            return -1
    
    @suppress_stderr
    def save_state(self):
        self.cached_state = self.llm.save_state()

    def load_state(self):
        self.llm.load_state(self.cached_state)
        
    def eval_question(
            self, 
            question_text: str, 
            verbose: int = 0,
        ) -> Dict:
        wrapped_text = wrap_prompt(usr_prompt=question_text)
        tokens_question = self.llm.tokenize(wrapped_text.encode())
        self.llm.eval(tokens_question)
        seed = self.gen_params.get('seed')
        if seed is not None: 
            self.llm.set_seed(seed)
        counter = 0
        completion = ''
        token = self.llm.sample(**get_sample_args(self.gen_params))
        while token is not self.llm.token_eos() :
            if counter >= self.gen_params.get('max_tokens', self.init_params.get('n_ctx')): 
                break
            else:
                counter += 1
            s_token = self.llm.detokenize([token]).decode()
            completion += s_token
            if verbose > 1:
                print(s_token, end='', flush=True)
            self.llm.eval([token])
            token = self.llm.sample(**get_sample_args(self.gen_params))
        if verbose > 1: print(end='\n', flush=True)
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
    def __init__(self) -> None:
        self.model: LocalModel = LocalModel(b_init=False)
        self.has_cache: bool = False
    def get(self, model_name:str=None, sys_prompt:str=None) -> LocalModel:
        if model_name is not None:
            if self.model.b_init is False:
                self.model.init(model_name)
            if self.has_cache:
                self.model.load_state()
            elif sys_prompt is not None:
                self.model.eval_prompt(sys_prompt)
                self.model.save_state()
                self.has_cache = True
                self.sys_prompt = sys_prompt
        return self.model
    

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
    

