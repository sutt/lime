import os
from dotenv import load_dotenv
import tiktoken
from openai import (
    OpenAI, 
    AuthenticationError,
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

def check_key_is_valid() -> bool:
    client = OpenAI(api_key=module_api_key)
    try:
        client.models.list()
        return True
    except AuthenticationError:
        return False
    except Exception as e:
        print(f'error in check_key_is_valid: {str(e)}')
        return False


def get_num_tokens(model_name: str, text: str) -> int:
    '''wont be exact due to system message payload style'''
    try:
        enc = tiktoken.encoding_for_model(model_name)
        return len(enc.encode(text))
    except:
        return -1


def submit_prompt(
    prompt: str,
    model_name: str,
    max_tokens: int = LocalParams.max_tokens,
    temperature: float = LocalParams.temperature,
) -> dict:

    client = OpenAI(
        api_key=module_api_key,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],    
        temperature=temperature,
        max_tokens=max_tokens,
        model=model_name,
    )

    return chat_completion


def get_completion(
    chat_completion: dict,
    role: str = "ai",
) -> str:

    return chat_completion.choices[0].message.content

