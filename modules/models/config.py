import os
import yaml

class ConfigLoader:
    __loaded_configs = {}
    __urn = {
        'data': lambda config: config,
        'keys': lambda data: data.keys(),
        'value': lambda data, key: data.get(key),
    }
    @classmethod
    def _load(cls, config_file):
        if config_file is None:
            return
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        if config is not None:
            cls.__loaded_configs = cls.__recursive_update(
                cls.__loaded_configs,
                config
            )
    @classmethod
    def _initialize(cls):
        urn = cls.__get_urn()
        try:
            data = urn.get('data')(cls.__loaded_configs)
            if data is not None:
                keys = urn.get('keys')(data)
                for key in keys:
                    value = urn.get('value')(data, key)
                    setattr(cls, key, value)
        except Exception as e:
            print(Warning(f'Error initializing {cls.__name__}'))
    @classmethod
    def _get_attrs(cls):
        return {k: v for k, v in cls.__dict__.items() 
                if not k.startswith('_')
        }
    @classmethod
    def __recursive_update(cls, original, updates):
        for key, value in updates.items():
            if isinstance(value, dict):
                original[key] = cls.__recursive_update(original.get(key, {}), value)
            else:
                original[key] = value
        return original
    @classmethod
    def __get_urn(cls):
        tmp_urn = cls.__urn.copy()
        if cls.__loaded_configs.get(cls.__name__) is not None:
            cls_name = cls.__name__
            tmp_urn.update({'data': lambda config: config.get(cls_name)})
        try: _urn = getattr(cls, '_urn')
        except: _urn = {}
        return {k: _urn.get(k) or default_v 
                for k, default_v in tmp_urn.items()
        }
    @classmethod
    def __rm_private_attrs(cls):
        for key in cls.__dict__.keys():
            if key.startswith('_'):
                try: delattr(cls, key)
                except: pass

# Priority (highest to lowest):
#  1. command line args  (not implemented yet)
#  2. workspace config
#  3. user config
#  4. defaults defined in class's source attributes

default_config_obj = {
    'LocalModels': {
        'llama_5t': {
            'fn': '/mnt/llamas/mega.gguf',
        },
    },
    'LocalParams': {
        'temperature': 0.0,
        'max_tokens': 20,
        'seed': None,
    },
    'DefaultSettings': {
        'input_sheet_prefix': 'input',
        'output_sheet_prefix': 'output',
    },
}
