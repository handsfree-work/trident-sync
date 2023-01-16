'''
options: #选项
  repo_root: repo         # submodule保存根目录
  push: true              # 同步后是否push
  pr: true                # 是否创建pr，需要目标仓库配置token和type
  proxy_fix: true         # 是否将https代理改成http://开头
  use_system_proxy: false  # 是否使用系统代理
'''
from lib.util import merge_from_dict


class Options:
    repo_root: str = 'repo'
    push: bool = True
    pr: bool = True
    proxy_fix: bool = True
    use_system_proxy: bool = True

    def __init__(self, conf_dict):
        merge_from_dict(self, conf_dict)
