import os

from lib.model.opts import Options
from lib.model.repo import RepoConf
from lib.model.sync import SyncTask
from lib.util import get_dict_value


class RunStatus:
    success: bool = False
    change: bool = False
    commit: bool = False
    push: bool = False


class Config:
    repo = {}
    sync = {}
    options: Options

    status: RunStatus

    def __init__(self, conf_dict):
        conf_repo = get_dict_value(conf_dict, 'repo')
        for key in conf_repo:
            self.repo[key] = RepoConf(key, conf_repo[key])
        conf_sync = get_dict_value(conf_dict, 'sync')
        for key in conf_sync:
            self.sync[key] = SyncTask(key, conf_sync[key], self.repo)
        conf_options = get_dict_value(conf_dict, 'options')
        self.status = RunStatus()
        self.options = Options(conf_options)

    def set_default_token(self, token=None):
        for key in self.repo:
            repo: RepoConf = self.repo[key]
            if repo.token:
                continue
            if not token:
                token = os.getenv(f'{repo.type}_token')
                if not token:
                    token = os.getenv(f'trident_token_{repo.type}')
            if token:
                repo.token = token
