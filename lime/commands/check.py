import os
import sys
import json
import pkg_resources
from typing import (
    Dict,
    Any,
)
from lime.common.models.state import (
    Secrets,
)
from lime.common.models.errs import (
    QuietError,
    BaseQuietError,
)
from lime.common.models.utils import (
    get_usr_config_dir,
    get_workspace_config_dir,
)
from lime.common.inference.base import (
    LocalParams,
)
from lime.common.inference.api_openai import (
    OpenAIModelObj,
)
from lime.common.inference.local_llama_cpp import (
    LocalModelFns,
    CppInference,
)
# TODO - add LocalParams and print out

def get_settings(obj) -> Dict:
    try:
        attrs = [a for a in dir(obj) if not a.startswith('_')]
        return {a: getattr(obj, a) for a in attrs}
    except:
        return {}

def fmt_grid(d: Dict, n_chars: int = 20) -> str:
    s = ''
    for k,v in d.items():
        # if not isinstance(v, str): continue
        row =  '{:<{n_chars}}'.format(k, n_chars=n_chars)
        row += ': '
        v = 'null' if v is None else v
        row += '{:<{n_chars}}'.format(v, n_chars=n_chars)
        row += '\n'
        s += row
    return s.rstrip()

def get_lime_version() -> str:
    try:
        version = pkg_resources.get_distribution("lime").version
    except pkg_resources.DistributionNotFound:
        version = "unknown"
    return version

def setup_parser(argparser):

    # NotImplemented
    argparser.add_argument('--full',        action='store_true')
    argparser.add_argument('--dataset',     action='store_true')
    argparser.add_argument('-b', '--debug', action='store_true')

def main(args):

    args = vars(args)

    if args.get('debug'):
        QuietError.debug_mode = True

    full_run = args.get('full')
    check_data = args.get('dataset')

    # Welcome message

    ## Current package
    msg = '### Lime'
    print(msg)
    
    msg = f'version: {get_lime_version()}'
    print(msg)

    ### Config Files Loaded
    msg = '\n### Config(s) Loaded'
    print(msg)

    usr_conf = get_usr_config_dir()
    ws_conf = get_workspace_config_dir()
    msg =  f'usr_config: {usr_conf is not None}\n'
    msg += f'ws_config:  {ws_conf is not None}'
    if ws_conf is not None:
        msg += f' | rel path: {os.path.relpath(ws_conf, os.getcwd())}'
    print(msg)


    ### OpenAI,
    msg = '\n### OpenAI'
    print(msg)

    #### api key
    msg = f'Secrets.OPENAI_API_KEY'
    key = Secrets.get('OPENAI_API_KEY')
    if key is not None:
        key_fmt = key[:4] + '****'
        infer_obj = OpenAIModelObj('gpt-3.5-turbo')
        try: is_valid = infer_obj.check_valid()
        except: is_valid = False
        msg += f': {key_fmt}  found. is_valid={is_valid}'
    else:
        msg += ' not found.'
    print(msg)


    ### LocalInference: Cpp
    msg = '\n### CppInference'
    print(msg)
    
    #### CppInference
    print(fmt_grid(get_settings(CppInference)))

    #### ModelFns
    # TODO - only print if model_type is 'local'
    d_modelfns = get_settings(LocalModelFns)
    print('')
    print(fmt_grid(d_modelfns))

    # TODO - check if model files exist and if they can tokenize
    # d_modelfns.

    ### InferenceParams:
    msg = '\n### InferenceParams'
    print(msg)

    #### LocalParams
    print(fmt_grid(get_settings(LocalParams)))

if __name__ == '__main__':
    main({})
