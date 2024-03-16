from typing import Union, Any, Dict, List
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
from .cpl_client import (
    infer_cpl,
    check_cpl,

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
    elif model_name.startswith('cpl'):
        b_valid = check_cpl()
        return b_valid
    elif llama_cpp_loaded:
        try: 
            _ = get_model_fn(model_name)
            return True
        except:
            return False
    else:
        return False


def count_tokens(text: str, model_name: str) -> int:
    if model_name.startswith('gpt') or model_name.startswith('cpl'):
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
    elif model_name.startswith('cpl'):
        try:
            answer = infer_cpl(
                prompt=(prompt_sys or '') + prompt_usr,
                sig_type='BasicQA',
            )
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

# refactor section

# break the valid_model_name into two parts


class ModelObj:
    def __self__(self, model_name: str):
        self.model_name : str = model_name
        self.gen_params : dict = {}
    def extract_gen_params(self, meta_data: dict) -> Dict[Any, Any]:
        return self.gen_params
    def set_gen_params(self, gen_params: dict) -> None:
        self.gen_params = self.validate_gen_params(gen_params)
    def check_valid(self, **kwargs) -> bool:
        raise NotImplementedError
    def count_tokens(self, text: str) -> int:
        raise NotImplementedError
    def validate_gen_params(self, gen_params: dict) -> dict:
        raise NotImplementedError    
    def prompt_model(self, 
                     prompt_sys: str, 
                     prompt_usr: str, 
                     progress_cb: callable = lambda x: None,
                     **kwargs
                     ) -> Any:
        raise NotImplementedError
    def parse_completion_obj(self, completion: Any) -> Any:
        raise NotImplementedError



class OpenAIModelObj(ModelObj):
    def __init__(self) -> None:
        super().__init__()

    def check_valid(self, **kwargs) -> bool:
        if not(check_key_is_valid()):
            raise ValueError('OpenAI API key not valid')
        return True


class LocalModelObj(ModelObj):
    def __init__(self) -> None:
        super().__init__()

    def check_valid(self, **kwargs) -> bool:
        _ = get_model_fn(self.model_name)
        return True


class CPLModelObj(ModelObj):
    def __init__(self) -> None:
        super().__init()

    def check_valid(self, **kwargs) -> bool:
        return check_cpl()

    def prompt_model(self, 
                     prompt_sys: str, 
                     prompt_usr: str, 
                     progress_cb: callable = None,
                     **kwargs
                     ) -> Any:
        return infer_cpl(
            prompt=(prompt_sys or '') + prompt_usr,
            sig_type='BasicQA',
        )

    def parse_completion_obj(self, completion: Any) -> Any:
        return completion

    def count_tokens(self, text: str) -> int:
        return get_num_tokens(text, self.model_name)

    def validate_gen_params(self, gen_params: dict) -> dict:
        return gen_params


# TODO - build a type of InferObj
# InferObj: Union[
#         OpenAIModelObj, 
#         LocalModelObj, 
#         CPLModelObj
#     ]:

def get_infer_obj(
        model_name: str
    ) -> Union[
        OpenAIModelObj, 
        LocalModelObj, 
        CPLModelObj
    ]:

    # TODO - check for model_name in configs, and it's associated type
    if model_name.startswith('gpt'):
        return OpenAIModelObj(model_name)
    
    elif model_name.startswith('cpl'):
        return CPLModelObj(model_name)
    
    elif llama_cpp_loaded:
        return LocalModelObj(model_name)
    
    else:
        raise ValueError(f'model_name {model_name} not recognized')

