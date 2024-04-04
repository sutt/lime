import os
import io
import ctypes
from contextlib import redirect_stderr
from typing import (
    Any,
    Dict,
    List,
    Union,
)
from .base import (
    PromptModelResponse,
    ModelObj,
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
except Exception as e:
    llama_cpp_loaded = False
    raise ValueError(f'exception in importing llama_cpp: {str(e)}')

llama_log_obj = []

class LocalModelFns(ConfigLoader):
    _urn = {
        'data': lambda config: config.get('LocalModels'),
        'value': lambda data, key: data.get(key, {}).get('fn'),
    }

LocalModelFns._initialize()


class CppInference:
    def _get_package_version(package_name: str) -> str:
        try: return __import__(package_name).__version__
        except: return 'unable to get version'
    default_package = 'llama_cpp'
    package_version = _get_package_version(default_package)


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
            msg = f'model_name {model_name} is not a valid file '
            msg += f'or list of LocalModelFns: {", ".join(list(LocalModelFns._to_dict().keys()))}'
            raise ValueError(msg)
    except Exception as e:
        raise ValueError(f'exception in get_model_fn: {e}')
        

def wrap_prompt(
        prompt:     Union[str, None] = None,
        sys_prompt: Union[str, None] = None,
        usr_prompt: Union[str, None] = None,
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

    
class LocalModelCache:
    
    def __init__(self) -> None:
        self.llm: Union[Llama, None] = None
        self.cached_state : Union[LlamaState, None] = None
    
    @suppress_stderr
    def save_state(self):
        self.cached_state = self.llm.save_state()

    def load_state(self):
        self.llm.reset()  # apply this if seed doesn't work?
        self.llm.load_state(self.cached_state)

    def eval_prompt(
            self, 
            prompt: str, 
            prompt_type : str ='prompt'
        ) -> None:
        wrapped_prompt = wrap_prompt(**{prompt_type: prompt})
        self.llm.eval(
            self.llm.tokenize(wrapped_prompt.encode())
        )
        
    def eval_sample_piecewise(
            self, 
            prompt: str, 
            progress_cb: callable = None,
        ) -> PromptModelResponse:
        
        try:
            self.eval_prompt(prompt=prompt, prompt_type='usr_prompt')
            
            if self.gen_params.get('seed') is not None: 
                self.llm.set_seed(self.gen_params.get('seed'))
            
            completion, counter = '', 1

            token = self.llm.sample(**get_sample_args(self.gen_params))
            
            while token is not self.llm.token_eos() :
                
                s_token = self.llm.detokenize([token]).decode()
                completion += s_token
                
                if progress_cb is not None:
                    progress_cb(s_token)

                if ((counter >= self.gen_params.get('max_tokens')) or  
                    (counter >= self.init_params.get('n_ctx'))      # TODO - split this off
                    ):
                    break
                else:
                    counter += 1

                self.llm.eval([token])
                token = self.llm.sample(**get_sample_args(self.gen_params))
            
            return PromptModelResponse(completion, None)
        
        except Exception as e:
            return PromptModelResponse(None, e)     #TODO - add completion to response
    


class LocalModelObj(ModelObj, LocalModelCache):
    
    def __init__(self, model_name: str, **kwargs) -> None:
        ModelObj.__init__(self, model_name, **kwargs)
        LocalModelCache.__init__(self)
        self.model_fn : str = get_model_fn(self.model_name)
        self.llm : Union[Llama, None] = None
        self.prompt_model_params : List[str] = [
            'temperature',
            'max_tokens',
            'seed',
        ]
        self.init_params = {
            'n_threads': 4,
            'n_ctx': 512,
        }

    def check_valid(self, **kwargs) -> bool:
        self.model_fn = get_model_fn(self.model_name)
        if self.llm is None:
            self.init_llm()
        return True
    
    @suppress_stderr
    def init_llm(self, **kwargs) -> None:
        llama_log_set(log_callback, ctypes.c_void_p())
        self.llm = Llama(
            model_path=get_model_fn(self.model_name), 
            vocab_only=kwargs.get('vocab_only', False),
            **self.init_params
        )
    
    def count_tokens(self, text: str) -> int:
        if self.llm is None:
            self.init_llm()
        try: return len(self.llm.tokenize(text.encode()))
        except: return -1
    
    @suppress_stderr
    def prompt_model(self,
            prompt_sys: str = None,
            prompt_usr: str = None,
            progress_cb: callable = None,
            **kwargs
        ) -> PromptModelResponse:

        try:

            if self.llm is None:
                self.init_llm()
                
            self.update_gen_params({
                k: v for k, v in kwargs.items()
                if k in self.prompt_model_params
            })
            
            if self.use_prompt_cache:
                
                self.load_state()

                return self.eval_sample_piecewise(
                    prompt=prompt_usr,
                    progress_cb=progress_cb,
                )
                
            else:
                
                return self.call_model(
                    prompt_sys=prompt_sys,
                    prompt_usr=prompt_usr,
                )
        
        except Exception as e:
            return PromptModelResponse(None, e)
        
    def call_model(self,
            prompt_sys: str = None,
            prompt_usr: str = None,
        ) -> PromptModelResponse:
        try:

            wrapped_prompt = wrap_prompt(
                sys_prompt=prompt_sys,
                usr_prompt=prompt_usr,
            )

            output = self.llm(
                prompt=wrapped_prompt, 
                **self.gen_params,
            )

            completion = self._get_completion(output)
            
            return PromptModelResponse(completion, None)
        
        except Exception as e:
            return PromptModelResponse(None, e)
    
    @staticmethod
    def _get_completion(output):
        return output['choices'][0]['text']



if __name__ == '__main__':
    
    print("start...\n")
    
    import time
    t0 = time.time()
    def mark():
        global t0
        print(f'{time.time()-t0:.2f}')
        t0 = time.time()

    # testing ConfigLoader
    # print(ConfigLoader.__loaded_configs)
    # print(list(LocalModelFns._get_attrs().items()))
    # print(LocalModelFns._get_attrs())
    # import sys
    # sys.exit()

    # v2 inference
    # prompt = 'Q: What is the largest planet? A:'
    # prompt = 'Q: Generate an esoteric french phrase. A:'
    # mark()
    # model = LocalModelObj('mistral_hf_7b')
    # mark()
    # model.init_llm()
    # mark()
    # answer = model.prompt_model(
    #     prompt_sys=None, 
    #     prompt_usr=prompt,
    #     max_tokens=10,
    # )
    # print(answer)
    # mark()
        
    #  v2.1 inference - using cache
    # sys_prompt = '''In the following answer only with lower case letters and no punctuation.'''
    # prompt = 'Q: Generate an esoteric french phrase. A:'
    # prompt = 'Q: In the following answer with German. Generate an esoteric phrase. A:'
    sys_prompt = '''In the following answer in German.'''
    prompt = 'Q: Generate an esoteric phrase. A:'
    mark()
    model = LocalModelObj(
        'mistral_hf_7b', 
        use_prompt_cache=True
    )
    mark()
    model.init_llm()
    if sys_prompt is not None:
        model.eval_prompt(
            prompt=sys_prompt, 
            prompt_type='sys_prompt'
        )
        model.save_state()
    mark()
    
    #  first call
    answer = model.prompt_model(
        prompt_sys=None, 
        prompt_usr=prompt,
        max_tokens=30,
        temperature=1.0,
        seed=1,
    )
    print(answer)
    mark()

    # next calls, to test seed: currently not working
    # answer = model.prompt_model(
    #     prompt_sys=None, 
    #     prompt_usr=prompt,
    #     max_tokens=30,
    #     temperature=1.0,
    #     seed=1,
    # )
    # print(answer)
    # mark()

    # answer = model.prompt_model(
    #     prompt_sys=None, 
    #     prompt_usr=prompt,
    #     max_tokens=30,
    #     temperature=1.0,
    #     seed=2,
    # )
    # print(answer)
    # mark()

    # answer = model.prompt_model(
    #     prompt_sys=None, 
    #     prompt_usr=prompt,
    #     max_tokens=30,
    #     temperature=1.0,
    #     seed=1,
    # )
    # print(answer)
    # mark()
    

