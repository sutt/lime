from typing import (
    Any,
    List,
    Dict,
    Union,
)
import requests
import tiktoken
from .base import (
    PromptModelResponse,
    ModelObj,
)
from ..models.state import (
    ConfigLoader,
    Secrets,
)

class CplServer(ConfigLoader):
    domain = 'localhost'
    port = 5000
    debug = True
CplServer._initialize()

class CplClientParams(ConfigLoader):
    valid_request_args = None  
CplClientParams._initialize()

class CPLModelObj(ModelObj):
    
    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)
        self.profile_params : Dict[str, Any] = {
            **CplClientParams._get_attrs().copy(), 
            **self.profile_params,  # base client params overidden by model specific profile vars
        }
        self.valid_request_args : Union[List[str], None] = CplClientParams.valid_request_args
        self.base_url : str = f'http://{CplServer.domain}:{CplServer.port}'
        self.endpoint_check : str = '/check'
        self.endpoint_infer : str = '/infer'

    def check_valid(self, **kwargs) -> bool:
        try:
            response = requests.get(
                self.base_url + self.endpoint_check,
                timeout=5
            )
            data = response.json() 
            if data.get('status') != 'ok':
                raise ValueError(f'Status not ok (cpl). Status: {data}')
            return True
        except Exception as e:
            raise ValueError(f'Exception in check_valid (cpl). Message: {str(e)}')

    def prompt_model(self, 
                     prompt_sys: str = None, 
                     prompt_usr: str = None, 
                     progress_cb: callable = None,
                     **kwargs
                     ) -> PromptModelResponse:
        
        try:
            
            req_params = {**self.profile_params.copy(), **kwargs}

            if self.valid_request_args:
                req_params = {
                    k:v for k,v in req_params.items() 
                    if k in self.valid_request_args
                }

            prompt = (
                (prompt_sys if prompt_sys else '') +
                (prompt_usr if prompt_usr else '')
            )
            
            payload = {
                'question': prompt,
                **req_params,
            }
            
            response = requests.post(
                self.base_url + self.endpoint_infer,
                json=payload
            )
            
            completion, error = None, None
            
            if response.status_code < 400:
                try:
                    result = response.json()
                    completion = result['answer']
                except Exception as e:
                    error = ValueError(f'Error parsing infer_cpl response: {e}')
            else:
                try: 
                    server_err_text = response.json().get('error')
                except: 
                    server_err_text = 'could not parse server error message'
                error = ValueError(f'Error: {response.status_code} - {server_err_text}')
            
            return PromptModelResponse(completion, error)
        
        except Exception as e:
            return PromptModelResponse(None, e)

    def parse_completion_obj(self, completion: Any) -> Any:
        return completion

    def count_tokens(self, text: str) -> int:
        '''TODO - switch on base model type: local or oai'''
        # m = LocalModel(self.model_name, vocab_only=True)
        # return m.num_tokens(text)
        try:
            return len(
                tiktoken.encoding_for_model(self.model_name)
                .encode(text)
            )
        except:
            return -1

    
