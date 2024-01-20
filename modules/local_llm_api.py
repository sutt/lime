import os
import io
import ctypes
from contextlib import redirect_stderr
from typing import (
    Dict,
)
from llama_cpp import (
    Llama, 
    LlamaState,
    llama_log_set, 
)

llama_log_obj = []

class LocalParams:  #TODO- rename default
    max_tokens = 50
    temperature = 0.0
    # TODO - load from data/config


class LocalModelFns:
    llama_7b = '../../../data/llama-2-7b.Q4_K_M.gguf'
    mistral_hf_7b = '../../../data/mistral-7b-instruct-v0.2.Q4_K_M.gguf'
    # default_model_name = "llama_7b"
    # TODO - load these from data

class ChatTemplate:
    full = None
    left = None
    right = None

class DefaultModelChatTemplates:
    llama_7b = {
        
    }
    mistral_hf_7b = {
        'full': '',
        'left': '',
        'right': '',
    }
    @classmethod
    def wrap_prompt(
            cls,
            prompt: str = None,
            sys_prompt: str = None,
            usr_prompt: str = None,
        ): 
        pass


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
        return getattr(LocalModelFns, model_name)
        # TODO check if model_fn exists
    except AttributeError:
        if os.path.isfile(model_name):
            return model_name
        else:
            msg = f'model_name {model_name} is not a valid file'
            msg += f'or list of LocalModelFns: {", ".join([""])}'
            msg += '\nadd '
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
    

class LocalModel:
    '''
        use python_llama_cpp for inference
    '''
    
    @suppress_stderr
    def __init__(self, model_name='llama_7b'):
        
        self.init_params = {
            'n_threads': 4,
        }
        self.generate_params = {
            'temperature': LocalParams.temperature,
            'max_tokens': LocalParams.max_tokens,
        }
        
        llama_log_set(log_callback, ctypes.c_void_p())
        
        self.llm : Llama = Llama(
            model_path=get_model_fn(model_name), 
            **self.init_params,
        )

        self.cached_state : LlamaState = None

    def __call__(self, prompt, **params):
        wrapped_prompt = wrap_prompt(prompt)
        output = self.llm(
            prompt=wrapped_prompt, 
            max_tokens=5,
            # **self.generate_params,
            
        )
        return output
    

    def eval_prompt(self, prompt):
        wrapped_prompt = wrap_prompt(sys_prompt=prompt)
        print(wrapped_prompt)
        tokenized_wrapped_prompt = self.llm.tokenize(wrapped_prompt.encode())
        self.llm.reset()
        self.llm.eval(tokenized_wrapped_prompt)  # **params_llm_eval
    
    @suppress_stderr
    def save_state(self, ):
        self.cached_state = self.llm.save_state()

    def load_state(self, ):
        self.llm.reset()
        self.llm.load_state(self.cached_state)
        
    
    def eval_question(
            self, 
            question_text: str, 
            seed: int = None, 
            max_tokens: int = 50, 
            verbose: int = 0,
        ) -> Dict:
        wrapped_text = wrap_prompt(usr_prompt=question_text)
        print(wrapped_text)
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
    def get(self, model_name:str, sys_prompt:str):
        if self.model is None:
            self.model = LocalModel(model_name)
        if self.has_cache:
            self.model.load_state()
        else:
            self.model.eval_prompt(sys_prompt)
            self.model.save_state()
            self.has_cache = True
    def eval_question(self, question_text:str, **params):
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





    # reset the obj and run
    # cache = LocalModelCache()
    # cache.get('mistral_hf_7b')
    # mark()
    # usr_prompt = 'What is the largest planet?'
    # t = cache(sys_prompt + usr_prompt)
    # print(LocalModel.get_completion(t))
    # mark()
    

