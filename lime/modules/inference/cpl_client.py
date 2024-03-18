from typing import (
    Any,
    Tuple,
    Union,
)
import requests
import tiktoken
from .base import (
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

configs = {
    # is api key needed by the client? ideally not just to reduce 
    # the surface area of exposing secrets
    'secrets': {
        'openai_api_key': Secrets.get('OPENAI_API_KEY'),
    },
    'settings': {
        'host': CplServer.domain,
        'port': CplServer.port,
        'debug': CplServer.debug,
        # TODO - add timeout
    }
}

def check_cpl(
        **kwargs
    ) -> bool:
    base_url = 'http://' + CplServer.domain + ':' + str(CplServer.port) + '/' 
    endpoint = 'check'
    try:
        response = requests.get(base_url + endpoint, timeout=5)
        data = response.json() 
        if data.get('status') != 'ok':
            raise ValueError(f'Error in cpl server check with status: {data}')
        return True
    except requests.exceptions.RequestException as e:
        raise ValueError(f'Error in cpl server check: {str(e)}')
    except Exception as e:
        raise ValueError(f'Error in cpl server check: {str(e)}')
    

class CPLModelObj(ModelObj):
    
    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)

    def check_valid(self, **kwargs) -> bool:
        return check_cpl()

    def prompt_model(self, 
                     prompt_sys: str = None, 
                     prompt_usr: str = None, 
                     progress_cb: callable = None,
                     **kwargs
                     ) -> Tuple[Union[str, None], Union[Exception, None]]:
        
        try:
            
            base_url = 'http://' + CplServer.domain + ':' + str(CplServer.port) + '/'
            end_point = 'infer'
            
            req_params = {}

            prompt = (
                (prompt_sys if prompt_sys else '') +
                (prompt_usr if prompt_usr else '')
            )
            
            data = {
                'question': prompt,
                **req_params,
            }
            
            response = requests.post(base_url + end_point, json=data)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    completion = result.get('answer')
                except Exception as e:
                    raise ValueError(f'Error parsing infer_cpl response: {e}')
            else:
                try: server_err_text = response.json().get('error')
                except: server_err_text = 'could not parse server error message'
                raise ValueError(f'Error: {response.status_code} - {server_err_text}')
            
            return (completion, None)
        
        except Exception as e:
            return (None, e)

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

    
