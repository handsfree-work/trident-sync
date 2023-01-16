import time

from lib.api.abstract_client import AbstractClient
from lib.http import Http, HTTPException
from lib.logger import logger
from lib.util import get_dict_value, re_pick


class GiteaClient(AbstractClient):
    '''gitee api'''
    '''
    https://gitee.com/api/v5/swagger#/postV5ReposOwnerRepoPulls
    '''

    def __init__(self, http, token, url):
        super().__init__(http, token, url)
        self.api_root = "https://gitee.com/api/v5"

    def post_pull_request(self, title, body, src_branch, target_branch):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls"
        res = self.http.post(api, data={
            "access_token": self.token,
            "title": title,
            "body": body,
            "head": f"{self.owner}:{src_branch}",
            "base": target_branch
        }, res_is_standard=False, res_is_json=True)
        return res

    def query_pull_request(self, src_branch, target_branch):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls?access_token={self.token}&head={self.owner}:{src_branch}&base={target_branch}&state=open"
        res = self.http.get(api, res_is_standard=False, res_is_json=True)
        if len(res) > 0:
            return res[0]
        return None

    def get_pull_request_detail(self, pull_id):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}?access_token={self.token}"
        res = self.http.get(api, res_is_standard=False, res_is_json=True)
        return res

    def put_merge(self, pull_id):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}/merge"
        self.http.put(api, data={
            "access_token": self.token
        }, res_is_standard=False, res_is_json=True)
