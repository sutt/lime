import requests
from .base import ModelObj

class AnthropicModelObj(ModelObj):
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = kwargs.get('api_key')
        self.temperature = kwargs.get('temperature', 0.0)
        self.max_tokens = kwargs.get('max_tokens', 20)
        self.seed = kwargs.get('seed')

    def prompt_model(self, prompt: str) -> str:
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        }
        data = {
            'model': self.model_name,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'seed': self.seed,
        }
        response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('content', [{}])[0].get('text', '')