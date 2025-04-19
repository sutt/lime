from typing import Union, Any, Dict, List
from ..models.state import (
    ConfigLoader,
    Secrets,
)
from ..models.config import default_config_obj
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

from .api_anthropic import (
    AnthropicModelObj, 
)

class ModelNameTypes(ConfigLoader):
    _urn = {
        'data': lambda config: config.get('LocalModels', {}),
        'value': lambda data, key: data.get(key,{}).get('type', 'local')
    }
ModelNameTypes._initialize()

class LocalParams(ConfigLoader):
    _urn = {
        'data': lambda config: config.get('LocalParams', default_config_obj.get('LocalParams', {})),
    }
LocalParams._initialize()

    
ModelObjVariant =  Union[
        OpenAIModelObj, 
        LocalModelObj, 
        CPLModelObj,
        AnthropicModelObj,
    ]


def get_infer_obj(model_name: str, **kwargs) -> ModelObjVariant:

    default_params = LocalParams._to_dict()

    params = {**default_params, **kwargs}

    model_type = None
    if model_name in ModelNameTypes._to_dict().keys():
        model_type = ModelNameTypes._to_dict()[model_name]
        if model_type not in ('openai', 'local', 'cpl', 'anthropic'):
            raise ValueError(f'model_type {model_type} not recognized')

    if ((model_type == 'openai') or
        (model_name.startswith('gpt') and (model_type is None))):
        return OpenAIModelObj(model_name, **params)
    
    elif ((model_type == 'cpl') or
          (model_name.startswith('cpl') and (model_type is None))):
        return CPLModelObj(model_name, **params)
    
    elif (model_type == 'local'):
        if not(llama_cpp_loaded):
            raise ValueError(f'llama_cpp not loaded; local model {model_name} not available')
        return LocalModelObj(
            model_name,
            use_prompt_cache = params.get('use_prompt_cache', False),
            **params
        )
    
    elif ((model_type == 'anthropic') or
          (model_name.startswith('claude') and (model_type is None))):
        if not Secrets.get('ANTHROPIC_API_KEY'):
            raise ValueError("Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
        return AnthropicModelObj(model_name, **params)
    
    elif llama_cpp_loaded:
        return LocalModelObj(
            model_name,
            use_prompt_cache = params.get('use_prompt_cache', False),
            **params
        )
    
    else:
        raise ValueError(f'model_name {model_name} not recognized.\n(note: llama_cpp not loaded)')

