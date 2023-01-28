'''
sync:
    task1:
        src: # 源仓库
          repo: fs-admin                  # 源仓库名称，上面repo配置的仓库名称引用
          dir: '.'                        #要同步给target的目录
        target: #目标仓库
          repo: test                      # 目标仓库名称，上面repo配置的仓库名称引用
          dir: 'package/ui/certd-client'  # 接收src同步过来的目录
          branch: 'client_sync'           # 同步分支名称（需要配置一个未被占用的分支名称）
'''
from lib.model.repo import RepoConf
from lib.util import merge_from_dict


class SyncTaskSrc:
    repo: str = None
    dir: str = None
    repo_ref: RepoConf

    def __init__(self, conf_dict):
        merge_from_dict(self, conf_dict)
        if not self.repo or not self.dir:
            raise Exception("sync.[key].src 中 < repo/dir > 必须配置")


class SyncTaskTarget:
    repo: str = None
    dir: str = None
    branch: str = None
    allow_reset_to_root: bool = True
    repo_ref: RepoConf

    def __init__(self, conf_dict):
        merge_from_dict(self, conf_dict)
        if not self.repo or not self.dir or not self.branch:
            raise Exception("sync.[key].target 中 < repo/dir/branch > 必须配置")


class SyncStatus:
    success: bool = False
    change: bool = False
    copy: bool = False
    commit: bool = False
    push: bool = False
    pr: bool = False
    merge: bool = False


class SyncTask:
    key: str = None
    src: SyncTaskSrc = None
    target: SyncTaskTarget = None
    copy_script: str = None

    status: SyncStatus

    def __init__(self, key, conf_sync: dict, repo_map):
        self.key = key

        if 'src' not in conf_sync:
            raise Exception(f"sync.{key}.src 必须配置")
        if 'target' not in conf_sync:
            raise Exception(f"sync.{key}.target 必须配置")

        merge_from_dict(self, conf_sync)
        self.status = SyncStatus()

        self.src = SyncTaskSrc(conf_sync['src'])
        self.target = SyncTaskTarget(conf_sync['target'])

        self.set_repo_ref(self.src, repo_map)
        self.set_repo_ref(self.target, repo_map)

    def set_repo_ref(self, task, repo_list):
        if task.repo in repo_list:
            task.repo_ref = repo_list[task.repo]
        else:
            raise Exception(f"任务[{self.key}]的{self.src.repo} 仓库配置不存在，请检查repo配置")
