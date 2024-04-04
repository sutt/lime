from typing import (
    List,
    Dict,
    Any,
)
from flask import (
    Flask, 
    Response,
    request, 
    jsonify,
)
from ..models.state import (
    ConfigLoader,
    Secrets,
)

class CplServerConfig(ConfigLoader):
    domain = 'localhost'
    port = 5000
    debug = False
    endpoint_check = 'check'
    endpoint_infer = 'infer'
CplServerConfig._initialize()

class CplServerParams(ConfigLoader):
    required_infer_keys = None
CplServerParams._initialize()

class CPLBaseServer:
    '''
        Import and inherit this class in your own app to create a server
        that can be used by the CPLModelObj client to make inference requests.
    '''
    def __init__(
            self, 
            server_config : Dict[str, Any] = {},
            server_params : Dict[str, Any] = {},
        ) -> None:

        self.app : Flask = Flask(__name__)
        self.server_config : Dict[str, Any] = {
            **CplServerConfig._to_dict(), 
            **server_config
        }
        self.server_params: Dict[str, Any] = {
            **CplServerParams._to_dict(),
            **server_params
        }
        self.secrets : Dict[str, Any] = Secrets.copy()
        self.required_infer_keys : List[str] = CplServerParams.required_infer_keys or []

        self.app.add_url_rule('/check', 'check_status', self.check_status)
        self.app.add_url_rule('/infer', 'infer', self.infer, methods=['POST'])

    def check_status(self) -> Response:
        '''
            Must return a JSON response with a status = 'ok'.
        '''
        return jsonify({
            'status': 'ok'
        })

    def infer(self) -> Response:
        '''
            Shouldnt need to override this method, instead:
             - override generate_answer()
             - add required keys to self.required_infer_keys
        '''
        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({'error': f'could not parse json payload: {str(e)}'}), 400
        
        try:
            self.check_payload(data)
        except AssertionError as e:
            return jsonify({'error': str(e)}) , 400
        
        try:
            answer = self.generate_answer(**data)
        except Exception as e:
            return jsonify({'error': f'Error on generate_answer: {str(e)}'}), 500

        return jsonify({'answer': answer}), 200
    
    def check_payload(self, data: dict, required_keys: list = ['question']) -> None:
        '''
            Raise Error if required keys are not found in payload.
            Inherit this method and modify self.required_infer_keys to add more checks.
        '''
        required_keys += self.required_infer_keys
        for key in required_keys:
            assert key in data, f'Key {key} not found in payload'

    def generate_answer(self, question: str, **kwargs) -> str:
        '''
            Override this method in the subclass to allow infer() to call it.
            Make sure to include kwargs so that client can pass extra args in payload.
        '''
        raise NotImplementedError

    def run(self, **kwargs):
        '''
            Call this method on your inherited class to start server.
            This is a blocking call, so save it for the end of your script.
        '''
        static_params = {
            'host':     self.server_config.get('host'),
            'port':     self.server_config.get('port'),
            'debug':    self.server_config.get('debug'),
        }
        run_server_params = {**static_params, **kwargs}

        self.app.run(**run_server_params)

