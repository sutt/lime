import os
import dotenv
from .config import ConfigLoader
from .utils import (
    get_usr_config_dir,
    get_workspace_config_dir,
)

Secrets = {}

usr_config_fn = get_usr_config_dir()

workspace_config_fn = get_workspace_config_dir()

if usr_config_fn is not None:
    ConfigLoader._load(usr_config_fn)

if workspace_config_fn is not None:
    ConfigLoader._load(workspace_config_fn)

# load secrets.env (if it exists in usr config) to env var 
if usr_config_fn is not None:
    secrets_fn = os.path.join(
        os.path.dirname(usr_config_fn),
        'secrets.env'
    )
    if os.path.exists(secrets_fn):
        dotenv.load_dotenv(secrets_fn)
        
# always try to load these secrets from env var
key_names = [
    'OPENAI_API_KEY',
]
for k in key_names:
    Secrets[k] = os.environ.get(k)
