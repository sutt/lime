from typing import Union, Any, Dict, List
from ..models.state import (
    ConfigLoader,
)
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


class ModelNameTypes(ConfigLoader):
    _urn = {
        'data': lambda config: config.get('LocalModels', {}),
        'value': lambda data, key: data.get(key,{}).get('type', 'local')
    }
ModelNameTypes._initialize()

    
ModelObjVariant =  Union[
        OpenAIModelObj, 
        LocalModelObj, 
        CPLModelObj,
    ]


def get_infer_obj(model_name: str, **kwargs) -> ModelObjVariant:

    model_type = None
    if model_name in ModelNameTypes._to_dict().keys():
        model_type = ModelNameTypes._to_dict()[model_name]
        if model_type not in ('openai', 'local', 'cpl'):
            raise ValueError(f'model_type {model_type} not recognized')

    if ((model_type == 'openai') or
        (model_name.startswith('gpt') and (model_type is None))):
        return OpenAIModelObj(model_name)
    
    elif ((model_type == 'cpl') or
          (model_name.startswith('cpl') and (model_type is None))):
        return CPLModelObj(model_name)
    
    elif (model_type == 'local'):
        if not(llama_cpp_loaded):
            raise ValueError(f'llama_cpp not loaded; local model {model_name} not available')
        return LocalModelObj(
            model_name,
            use_prompt_cache = kwargs.get('use_prompt_cache', False)
        )
    
    elif llama_cpp_loaded:
        return LocalModelObj(
            model_name,
            use_prompt_cache = kwargs.get('use_prompt_cache', False)
        )
    
    else:
        raise ValueError(f'model_name {model_name} not recognized.\n(note: llama_cpp not loaded)')

