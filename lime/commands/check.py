import os
import sys
import json
import pkg_resources
from typing import (
    Dict,
    List,
    Any,
)
from lime.common.models.state import (
    Secrets,
)
from lime.common.models.errs import (
    NetworkError,
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
from lime.common.inference.interface import (
    ModelNameTypes,
)
from lime.common.inference.api_openai import (
    OpenAIModelObj,
    ApiModelName,
)
from lime.common.inference.local_llama_cpp import (
    LocalModelFns,
    CppInference,
)
from lime.common.inference.cpl_client import (
    CplClientParams,
    CPLModelObj,
)
from lime.common.inference.cpl_server import (
    CplServerParams,
    CplServerConfig,
)

def get_settings(obj) -> Dict[str, Any]:
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

def get_pkg_version(pkg: str) -> str:
    try:
        version = pkg_resources.get_distribution(pkg).version
    except pkg_resources.DistributionNotFound:
        version = "unknown"
    return version

def get_model_by_type(model_type: str) -> List[str]:
    try:
        d = ModelNameTypes._to_dict()
        return [k for k,v in d.items() if v == model_type]
    except:
        return []
    

def setup_parser(argparser):

    # NotImplemented
    argparser.add_argument('--dataset',         action='store_true')
    argparser.add_argument('-v', '--verbose',   action='store_true')
    argparser.add_argument('-b', '--debug',     action='store_true')

def main(args):

    args = vars(args)

    if args.get('debug'):
        QuietError.debug_mode = True

    check_data = args.get('dataset')
    verbose = args.get('verbose')

    # Welcome message

    ## Current package
    msg = '### Lime'
    print(msg)
    
    msg = f'version: {get_pkg_version("lime")}'
    print(msg)

    ### Config Files Loaded
    msg = '\n### Configs Loaded'
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
        try: 
            is_valid = infer_obj.check_valid()
        except NetworkError:
            is_valid = 'n/a (no network conn)'
        except: 
            is_valid = False
        msg += f': {key_fmt}  found. is_valid={is_valid}'
    else:
        msg += ' not found.'
    print(msg)

    # package version
    msg = f'version: {get_pkg_version("openai")}'
    print(msg)

    print('\n##### Custom OpenAI Models')
    d_modelfns = {
        model_name: model_info
        for model_name, model_info in ApiModelName._to_dict().items()
        if model_name in get_model_by_type('openai')
    }
    print(fmt_grid(d_modelfns))

    ### LocalInference: Cpp
    msg = '\n### LlamaCpp Inference'
    print(msg)
    
    #### CppInference
    # TODO - check if llama is installed
    print(fmt_grid(get_settings(CppInference)))

    #### ModelFns
    print('\n#### Custom Local Models')
    d_modelfns = {
        model_name: model_info
        for model_name, model_info in LocalModelFns._to_dict().items()
        if model_name in get_model_by_type('local')
    }
    print(fmt_grid(d_modelfns))

    ### InferenceParams:
    msg = '\n### InferenceParams'
    print(msg)

    print(fmt_grid(get_settings(LocalParams)))
    
    ### CPL
    msg = '\n### CPL'
    print(msg)

    if not verbose: 
        print("(re-run with -v / --verbose flag to view these)")
    else:
        print('#### CplServerConfig')
        print(fmt_grid(get_settings(CplServerConfig)))
        print('#### CplServerParams')
        print(fmt_grid(get_settings(CplServerParams)))
        print('#### CplClientParams')
        print(fmt_grid(get_settings(CplClientParams)))

        print('#### Custom Cpl Models')
        d_modelfns = {
            model_name: model_info
            for model_name, model_info in LocalModelFns._to_dict().items()
            if model_name in get_model_by_type('cpl')
        }
        print(fmt_grid(d_modelfns))

        print('#### CPLServer Status Check')
        print('checking...', end='', flush=True)
        
        is_valid, err_msg = False, ''
        try:
            is_valid = CPLModelObj('my_cpl_basic').check_valid()
        except Exception as e:
            is_valid = False
            err_msg = str(e)
        msg = f'server {"is live" if is_valid else "is down"} ({err_msg[:20]}...)'
        print(msg, end='\n', flush=False)


if __name__ == '__main__':
    main({})
