from typing import (
    Any,
    Tuple,
    Union,
)
import tiktoken
from openai import (
    OpenAI, 
    AuthenticationError,
    ChatCompletion,
)
from .base import (
    ModelObj,
)
from ..models.state import (
    ConfigLoader,
    Secrets,
)

class LocalParams(ConfigLoader):
    max_tokens = 50
    temperature = 0.0

LocalParams._initialize()


module_api_key = Secrets.get('OPENAI_API_KEY')


class OpenAIModelObj(ModelObj):

    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)
        self.prompt_model_params = [
            'temperature',
            'max_tokens',
        ]

    def check_valid(self, **kwargs) -> bool:
        client = OpenAI(api_key=module_api_key)
        try: client.models.list()
        except AuthenticationError:
            raise AuthenticationError('OpenAI API key not valid')
        except Exception as e:
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
                    ) -> Tuple[Union[str, None], Union[Exception, None]]:
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
                model=self.model_name,
                **params,
            )

            s_completion = self._get_completion(chat_completion)
            
            return s_completion, None
        
        except Exception as e:
            
            return None, e
    
    @staticmethod
    def _get_completion(chat_completion: ChatCompletion) -> str:
        return chat_completion.choices[0].message.content
        

