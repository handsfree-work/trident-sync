import time

from lib.api.abstract_client import AbstractClient
from lib.http import Http, HTTPException
from lib.logger import logger
from lib.util import get_dict_value


class GithubClient(AbstractClient):
    '''github api'''
    # 下面定义了一个类属性
    token = 'token'
    http = None
    url = None
    repo_path = None
    owner = None
    repo = None
    headers = None;

    def __init__(self, http, token, url):
        super().__init__(http, token, url)

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def post_pull_request(self, title, body, src_branch, target_branch):
        api = f"https://api.github.com/repos/{self.repo_path}/pulls"
        res = self.http.post(api, data={
            "title": title,
            "body": body,
            "head": f"{self.owner}:{src_branch}",
            "base": target_branch,
            "maintainer_can_modify": True
        }, headers=self.headers, res_is_standard=False, res_is_json=True)
        return res

    def query_pull_request(self, src_branch, target_branch):
        api = f"https://api.github.com/repos/{self.repo_path}/pulls?head={self.owner}:{src_branch}&base={target_branch}&state=open"
        res = self.http.get(api, headers=self.headers, res_is_standard=False, res_is_json=True)
        if len(res) > 0:
            return res[0]
        return None

    def get_pull_request_detail(self, pull_id):
        api = f"https://api.github.com/repos/{self.repo_path}/pulls/{pull_id}"
        res = self.http.get(api, headers=self.headers, res_is_standard=False, res_is_json=True)
        return res

    def put_merge(self, pull_id):
        api = f"https://api.github.com/repos/{self.repo_path}/pulls/{pull_id}/merge"
        self.http.put(api, data={}, headers=self.headers, res_is_standard=False, res_is_json=True)
