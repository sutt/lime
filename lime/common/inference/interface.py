from typing import Union, Any, Dict, List
from .api_openai import (
    OpenAIModelObj,
)
from .local_llama_cpp import (
    LocalModelObj,
    llama_cpp_loaded,
)
from .cpl_client import (
    CPLModelObj,
)


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


ModelObjVariant =  Union[
        OpenAIModelObj, 
        LocalModelObj, 
        CPLModelObj,
    ]


def get_infer_obj(model_name: str, **kwargs) -> ModelObjVariant:

    # TODO - check for model_name in configs, and it's associated type
    if model_name.startswith('gpt'):
        return OpenAIModelObj(model_name)
    
    elif model_name.startswith('cpl'):
        return CPLModelObj(model_name)
    
    elif llama_cpp_loaded:
        return LocalModelObj(
            model_name,
            use_prompt_cache = kwargs.get('use_prompt_cache', False)
        )
    
    else:
        raise ValueError(f'model_name {model_name} not recognized')

