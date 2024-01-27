from .config import ConfigLoader
from .utils import (
    get_usr_config_dir,
    get_workspace_config_dir,
)

usr_config_fn = get_usr_config_dir()

workspace_config_fn = get_workspace_config_dir()

ConfigLoader._load(usr_config_fn)

ConfigLoader._load(workspace_config_fn)