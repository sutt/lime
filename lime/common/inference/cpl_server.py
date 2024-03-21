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

class CplServer(ConfigLoader):
    domain = 'localhost'
    port = 5000
    debug = False

# Since I'm inheriting the server base class, as opposed to 
# running a script, will this ever find a workspace config file?
CplServer._initialize()

CONFIGS = {
    'secrets': {
        'openai_api_key': Secrets.get('OPENAI_API_KEY'),
    },
    'settings': {
        'host': CplServer.domain,
        'port': CplServer.port,
        'debug': CplServer.debug,
    }
}

class CPLBaseServer:
    def __init__(self, config:dict = {}) -> None:
        self.app = Flask(__name__)
        self.config = {**CONFIGS, **config}
        self.infer_obj = None

        self.app.add_url_rule('/check', 'check_status', self.check_status)
        
        self.app.add_url_rule('/infer', 'infer', self.infer, methods=['POST'])

    def check_status(self) -> Response:
        # TODO - check if infer model is loaded
        # TODO - add checks for other services, e.g. retrieval connection etc
        return jsonify({
            'status': 'ok'
        })

    def infer(self) -> Response:
        data = request.get_json()
        question = data.get('question')
        # TODO - get extra params to send as args to generate_answer
        # if specified as a type of something, e.g. sig_type[Optional[str]] these
        # can be programmatically parsed here, but also referenced in check_status
        if question is None:
            return jsonify({'error': 'No question provided in json body'}, 400)
        try:
            answer = self.generate_answer(question)
        except Exception as e:
            return jsonify({'error': f'Error when calling generate_answer{str(e)}'}, 500)
        response = {'answer': answer}
        return jsonify(response)

    def generate_answer(self, question: str, **kwargs) -> str:
        # Override this method in the subclass to generate an answer 
        # using the infer_obj
        return "CPLBaseServer default answer"

    def run(self, **kwargs):
        run_params = {
            'host':     self.config.get('settings').get('host'),
            'port':     self.config.get('settings').get('port'),
            'debug':    self.config.get('settings').get('debug'),
        }
        params = {**kwargs, **run_params}
        # TODO - verbose option
        # TODO try/catch keyboard interrupt
        self.app.run(**params)


# class InferObj:
#     def __init__(self, **kwargs):
#         self.setup_client_objs(**kwargs)
#     def setup_client_objs(self, **kwargs):
#         pass
#         # self.turbo = dspy.OpenAI(
#         #     model='gpt-3.5-turbo', 
#         #     api_key=OPENAI_API_KEY,
#         # )
#         # self.colbertv2_wiki17_abstracts = dspy.ColBERTv2(
#         #     url='http://

# class CPLServer(CPLBaseServer):
#     def __init__(self, InferObj, config: dict = None):
#         super().__init__(config)
#         self.api_key = config['api_key']
#         # Initialize the InferObj using the config variables
#         self.infer_obj = InferObj(api_key=self.api_key)

#     def process_data(self, data):
#         # Custom implementation to process the received JSON data
#         processed_data = self.infer_obj.preprocess_data(data)
#         return {
#             'message': 'JSON data processed using InferObj', 
#             'data': processed_data
#         }

#     def generate_answer(self, question):
#         # Custom implementation to generate an answer using the infer_obj
#         answer = self.infer_obj.generate_answer(question, sig_type='BasicQA')
#         return answer
