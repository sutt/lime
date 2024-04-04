from typing import (
    Any,
    Tuple,
    Union,
)
import requests
import tiktoken
from openai import (
    OpenAI, 
    AuthenticationError,
    ChatCompletion,
)
from .base import (
    PromptModelResponse,
    ModelObj,
)
from ..models.errs import (
    NetworkError,
)
from ..models.state import (
    ConfigLoader,
    Secrets,
)

module_api_key = Secrets.get('OPENAI_API_KEY')

class ApiModelName(ConfigLoader):
    _urn = {
        'data': lambda config: config.get('LocalModels'),
        'value': lambda data, key: (
            data.get(key, {}).get('api_model_name')
        )
    }
ApiModelName._initialize()


class OpenAIModelObj(ModelObj):

    def __init__(
            self, 
            model_name: str,
            **kwargs
        ) -> None:
        super().__init__(model_name, **kwargs)
        self.prompt_model_params = [
            'temperature',
            'max_tokens',
            'seed',
        ]
        self.api_model_name =(
            ApiModelName._to_dict().get(model_name) or 
            kwargs.get('api_model_name') or
            self.model_name
        )

    def check_valid(self, **kwargs) -> bool:
        try: 
            client = OpenAI(api_key=module_api_key)
            models_list = client.models.list()
            if self.api_model_name not in [m.id for m in models_list.data]:
                raise ValueError(f'model `{self.api_model_name}` not found in models list')
        # TODO - check if network connections is available
        except AuthenticationError:
            raise AuthenticationError('OpenAI API key not valid')
        except Exception as e:
            try: requests.get('https://www.google.com/', timeout=2)
            except requests.ConnectionError:
                raise NetworkError('No network connection available')
            raise ValueError(f'error in check_key_is_valid: {str(e)}')
        return True
    
    def count_tokens(self, text: str) -> int:
        '''wont be exact due to system message payload style'''
        try:
            return len(
                tiktoken.encoding_for_model(self.model_name)
                .encode(text)
            )
        except:
            return -1
    
    def prompt_model(self, 
                     prompt_sys: str, 
                     prompt_usr: str, 
                     progress_cb: callable = None,
                     **kwargs
                    ) -> PromptModelResponse:
        try:

            client = OpenAI(
                api_key=module_api_key,
            )

            params = self.gen_params.copy()
            
            params.update({
                k: v 
                for k, v in kwargs.items()
                if k in self.prompt_model_params
            })

            prompt = (
                (prompt_sys if prompt_sys else '') +
                (prompt_usr if prompt_usr else '')
            )
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],    
                model=self.api_model_name,
                **params,
            )

            s_completion = self._get_completion(chat_completion)
            
            return PromptModelResponse(s_completion, None)
        
        except Exception as e:
            
            return PromptModelResponse(None, e)
    
    @staticmethod
    def _get_completion(chat_completion: ChatCompletion) -> str:
        return chat_completion.choices[0].message.content
        

if __name__ == '__main__':

    import time
    t0 = time.time()
    def mark():
        global t0
        print(f'{time.time()-t0:.2f}')
        t0 = time.time()

    prompt = 'Q: What is the largest planet? A:'
    # prompt = 'Q: Generate an esoteric french phrase. A:'
    # prompt = 'Q: Generate an esoteric french phrase. (Then explain why it would be considered esoteric) A:'
    mark()
    model = OpenAIModelObj('gpt-3.5-turbo')
    mark()
    answer = model.prompt_model(
        prompt_sys=None, 
        prompt_usr=prompt
    )
    print(answer)
    mark()

    