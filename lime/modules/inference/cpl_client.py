import requests

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

def infer_cpl(
        prompt: str,
        sig_type: str = None,  # make this to kwargs type
    ) -> str:
    
    base_url = 'http://' + CplServer.domain + ':' + str(CplServer.port) + '/'
    end_point = 'infer'
    
    req_params = {}
    req_params['sig_type'] = 'BasicQA',    # default for now
    if sig_type is not None:
        req_params['sig_type'] = sig_type
    
    data = {
        'question': prompt,
        **req_params,
    }
    
    response = requests.post(base_url + end_point, json=data)
    
    if response.status_code == 200:
        try:
            result = response.json()
            return result.get('answer')
        except Exception as e:
            raise ValueError(f'Error parsing infer_cpl response: {e}')
    else:
        try: server_err_text = response.json().get('error')
        except: server_err_text = 'could not parse server error message'
        raise ValueError(f'Error: {response.status_code} - {server_err_text}')
    
def check_cpl(
        **kwargs
    ) -> bool:
    base_url = 'http://' + CplServer.domain + ':' + str(CplServer.port) + '/' 
    endpoint = 'check'
    try:
        response = requests.get(base_url + endpoint, timeout=5)
        data = response.json() 
        if data.get('status') != 'ok':
            return False
        return True
    except Exception as e:
        print(f'Error checking cpl server: {e}')
        return False
    
