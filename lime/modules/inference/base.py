from typing import (
    Union, 
    Any, 
    Dict, 
    List,
    Tuple,
)

class ModelObj:
    def __init__(self, model_name: str) -> None:
        self.model_name : str = model_name
        self.gen_params : Dict[str, Any] = {}
        self.prompt_model_params : List[str] = []
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
                     ) -> Tuple[Union[str, None], Union[Exception, None]]:
        '''
        return (completion, error)
        '''
        raise NotImplementedError
