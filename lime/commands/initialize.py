import os
import shutil
from lime.common.models.errs import (
    BaseQuietError,
)


'''
Utility to help write out the following directory/files:
    - template configs: 
        - format: .lime/config.yaml
        - type=workspace: write to current working directory
        - type=usr: write to user home directory
    - datasets: 
        - simple: .lime/data/datasets/simple
        - variety: .lime/data/datasets/variety (not implemented)        

'''

def config_init(
        config_type: str = 'workspace',
) -> None:

    if config_type == 'workspace':
        write_dir = os.getcwd()
    elif config_type == 'usr':
        write_dir = os.path.expanduser('~')
    else:
        raise BaseQuietError(f'config_type: {config_type} must be `workspace` or `usr`')

    script_dir = os.path.dirname(os.path.abspath(__file__))

    write_fn = 'config.yaml'
    config_dir = '.lime'
    
    if os.path.isdir(os.path.join(write_dir, config_dir)):
        raise BaseQuietError(f'.lime directory already exists in current working directory: {write_dir}')
    
    try:
        os.mkdir(os.path.join(write_dir, config_dir))
    except:
        raise BaseQuietError(f'failed to create .lime directory in current working directory: {write_dir}')

    write_fn = os.path.join(write_dir, config_dir, write_fn)

    read_fn = 'template.yaml'
    read_fn = os.path.join(script_dir, '..' 'data', 'config_model', read_fn )

    #  read from template and write to config.yaml
    with open(read_fn, 'r') as f:
        template = f.read()

    with open(write_fn, 'w') as f:
        f.write(template)

    if config_type == 'usr':
        
        place = os.path.join(write_dir, config_dir)
        
        fn = os.path.join(place, '.gitignore')
        contents = 'secrets.env\n'
        with open(fn, 'w') as f:
            f.write(contents)

        fn = os.path.join(place, 'secrets.env')
        contents = '#OPENAI_API_KEY=sk...\n'
        with open(fn, 'w') as f:
            f.write(contents)

def dataset_init(
        dataset_type: str = 'simple',
) -> None:
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    write_dir = os.getcwd()

    if dataset_type == 'simple':
        dataset_root_dir = 'simple'
    elif dataset_type == 'variety':
        dataset_root_dir = 'variety'
        raise NotImplementedError('variety dataset not yet implemented')
    else:
        raise BaseQuietError(f'dataset_type: {dataset_type} not recognized')
    
    read_datasets_root = os.path.join(
        script_dir, 
        '..',
        'data', 
        'datasets',
        dataset_root_dir,
        )
    
    # copy all files and directories from read_datasets_root to write_dir
    # autogenerated...
    for fn in os.listdir(read_datasets_root):
        read_fn = os.path.join(read_datasets_root, fn)
        write_fn = os.path.join(write_dir, fn)
        if os.path.isfile(read_fn):
            with open(read_fn, 'r') as f:
                template = f.read()
            with open(write_fn, 'w') as f:
                f.write(template)
        elif os.path.isdir(read_fn):
            shutil.copytree(read_fn, write_fn)
        else:
            raise BaseQuietError(f'file type not recognized: {read_fn}')
    
    return
        


def setup_parser(argparser):

    argparser.add_argument('init_type', nargs='?', default=None
                          ,help='type of init: `config` or `data`')
    
    # config init options
    argparser.add_argument('--usr',         action='store_true')
    argparser.add_argument('--workspace',   action='store_true')
    argparser.add_argument('--bare',        action='store_true')

    # data init options
    argparser.add_argument('--simple',      action='store_true')
    argparser.add_argument('--variety',     action='store_true')


def main(args):
    
    args = vars(args)

    init_type = args.get('init_type')

    if init_type is None:
        raise BaseQuietError('Missing Required Arg: `init_type`')
    
    if init_type == 'config':
        
        config_type = 'workspace' 
        if args.get('usr'):
            config_type = 'usr'

        config_init(
            config_type = config_type,
        )

    elif init_type == 'dataset':
        
        dataset_type = 'simple' 
        if args.get('variety'):
            dataset_type = 'variety'
        
        dataset_init(
            dataset_type = dataset_type,
        )

    else:
        raise BaseQuietError(f'init_type: {init_type} must be `config` or `dataset`')
    
    return