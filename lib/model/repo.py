'''
repo:
  test: # 你的项目（接受同步项目），可以任意命名
    url: "https://github.com/handsfree-work/trident-test"           # 仓库地址
    path: "target"                    # submodule子路径
    branch: "main"                    # 你的代码开发主分支（接受合并的分支）例如dev、main等
    token: ""                         # 仓库token，用于提交PR, 前往 https://github.com/settings/tokens 创建token
    type: github                      # 仓库类型，用于提交PR，可选项：[github/gitee/gitea/gitlab]
'''
from lib.util import merge_from_dict


class RepoConf:
    key: str = None

    # submodule相关
    url: str = None
    branch: str = None
    path: str = None

    # pr 相关
    token: str = None
    type: str = None
    auto_merge: bool = True

    def __init__(self, key, conf_dict: dict):
        self.key = key
        merge_from_dict(self, conf_dict)
        if not self.url or not self.branch or not self.path:
            raise Exception(f"repo<{key}> 中 url/branch/path 必须配置")

        if self.url.startswith("https://github.com"):
            self.type = 'github'
        elif self.url.startswith("https://gitee.com"):
            self.type = 'gitee'
