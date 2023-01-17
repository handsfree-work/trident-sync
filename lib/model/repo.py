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


class RepoRef:
    url: str
    branch: str
    path: str
    token: str
    type: str

    def __init__(self, conf_dict):
        merge_from_dict(self, conf_dict)
        if not self.url or not self.branch or not self.path:
            raise Exception("repo中 < url/branch/path > 必须配置")
