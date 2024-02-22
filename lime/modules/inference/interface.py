from typing import Union, Any
from .oai_api import (
    submit_prompt, 
    get_completion,
    check_key_is_valid,
    get_num_tokens
)
from .local_cpp import (
    LocalModel,
    LocalModelCache,
    llama_cpp_loaded,
    get_model_fn,
)


class ModelCacheFactory:
    def __init__(self):
        self.instance = LocalModelCache()
    def get(self) -> LocalModelCache:
        return self.instance
    

def valid_model_name(model_name: str) -> bool:
    if model_name.startswith('gpt'):
        if check_key_is_valid():
            return True
        return False
    elif llama_cpp_loaded:
        try: 
            _ = get_model_fn(model_name)
            return True
        except:
            return False
    else:
        return False


def count_tokens(text: str, model_name: str) -> int:
    if model_name.startswith('gpt'):
        return get_num_tokens(text, model_name)
    else:
        m = LocalModel(model_name, vocab_only=True)
        return m.num_tokens(text)


def extract_gen_params(meta_data: dict) -> dict:
    params = {
        'temperature': float,
        'max_tokens': int,
        'seed': int,
    }
    gen_params = {}
    for k, f in params.items():
        if k in meta_data:
            try: gen_params[k] = f(meta_data[k])
            except: pass
    return gen_params


def prompt_model(
    model_name: str,
    prompt_sys: str = None,
    prompt_usr: str = None,
    model_cache: Union[None, LocalModelCache] = None,
    verbose : int = 0,
    gen_params: dict = {},
):
    error = None
    if model_name.startswith('gpt'):
        try:
            completion = submit_prompt(
                prompt=(prompt_sys or '') + prompt_usr,
                model_name=model_name,
                **gen_params,
            )
            answer = get_completion(completion)
        except Exception as e:
            error = e
            answer = None

    elif llama_cpp_loaded:        
        try:
            if ((model_cache is not None) and
                (prompt_sys is not None) and 
                (prompt_usr is not None)
                ):
                model = model_cache.get(model_name, prompt_sys)
                model.set_gen_params(gen_params)
                output = model.eval_question(prompt_usr, verbose)
                answer = output.get('text')
            else:
                model = LocalModel(model_name)
                model.set_gen_params(gen_params)
                output = model( (prompt_sys or '') + prompt_usr)
                answer = LocalModel.get_completion(output)
        except Exception as e:
            # TODO - configurable to raise err if needed
            # import traceback
            # traceback.print_exc()
            error = e
            answer = None
    else:
        # TODO - this should raise an err, no reason to continue an eval
        #        since we'll never create a completion
        error = 'not an openai model, llama_cpp not loaded'
        answer = None

    return answer, error
