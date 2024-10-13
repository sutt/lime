import requests

class AnthropicModelObj:
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.api_key = kwargs.get('api_key')
        self.temperature = kwargs.get('temperature', 0.0)
        self.max_tokens = kwargs.get('max_tokens', 20)
        self.seed = kwargs.get('seed')

    def _get_completion(self, prompt: str) -> str:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        data = {
            'model': self.model_name,
            'prompt': prompt,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'seed': self.seed,
        }
        response = requests.post('https://api.anthropic.com/v1/completions', headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('completion', '')