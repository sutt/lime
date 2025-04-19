import requests
from .base import ModelObj
from ..models.state import Secrets

class AnthropicModelObj(ModelObj):
    def __init__(self, model_name: str, **kwargs):
        
        if model_name.startswith('claude-'):

            model_name = model_name.replace('.', '-')
            
            model_mapping = {
                'claude-3-opus': 'claude-3-opus-20240229',
                'claude-3-sonnet': 'claude-3-sonnet-20240229',
                'claude-3-haiku': 'claude-3-haiku-20240307',
                'claude-3-5-sonnet': 'claude-3-5-sonnet-20240620',
            }
            
            for base_name, full_name in model_mapping.items():
                if model_name == base_name or model_name.startswith(f"{base_name}-"):

                    if len(model_name.split('-')) <= 4:
                        model_name = full_name
                    break
            
        super().__init__(model_name, **kwargs)
        self.api_key = kwargs.get('api_key') or kwargs.get('anthropic_api_key') or Secrets.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable or provide it in kwargs.")
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