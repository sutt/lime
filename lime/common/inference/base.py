from typing import (
    Union, 
    Any, 
    Dict, 
    List,
    Tuple,
    NamedTuple,
)
from ..models.state import (
    ConfigLoader,
)

class LocalParams(ConfigLoader):
    max_tokens = 100
    temperature = 0.0
    seed = None
LocalParams._initialize()

class ModelProfileParams(ConfigLoader):
    '''
        ModelProfileParams not ._initialized() until a 
        model is instantiated and can know model_name
    '''
    @classmethod
    def _initialize_for_model(cls, model_name: str):
        cls._urn = {
            'data': lambda config: (
                config.get('LocalModels', {})
                        .get(model_name, {})
                        .get('profile', {})
            )
        }
        cls._initialize()
        
class PromptModelResponse(NamedTuple):
    '''
        All model objects .prompt_model() methods 
        should return this response object.
    '''
    completion: Union[str, None]
    error:      Union[Exception, None]

class ModelObj:
    '''
        Base class for all model object variants.
        - Sets the base attributes for all model objects,
        - Defines the required methods that must be implemented
    '''
    def __init__(self, model_name: str, **kwargs) -> None:
        
        self.model_name : str = model_name
        self.use_prompt_cache : bool = kwargs.get('use_prompt_cache', False)
        self.gen_params : Dict[str, Any] = LocalParams._to_dict()
        self.prompt_model_params : List[str] = []
        
        ModelProfileParams._initialize_for_model(model_name)
        self.profile_params = ModelProfileParams._to_dict()
        self.gen_params = {
            k: self.profile_params.get(k) or v
            for k, v in self.gen_params.items()
        }    
    def get_gen_params(self) -> Dict[str, Any]:
        return self.gen_params
    def update_gen_params(self, gen_params: dict) -> None:
        self.gen_params.update(
            self.validate_gen_params(gen_params)
        )
    def validate_gen_params(self, gen_params: dict) -> dict:
        return gen_params
    def check_valid(self, **kwargs) -> bool:
        raise NotImplementedError
    def count_tokens(self, text: str) -> int:
        raise NotImplementedError
    def prompt_model(self, 
                     prompt_sys: str = None, 
                     prompt_usr: str = None, 
                     progress_cb: callable = None,
                     **kwargs
                     ) -> PromptModelResponse:
        raise NotImplementedError
