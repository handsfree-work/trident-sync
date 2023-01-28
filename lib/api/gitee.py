import time

from lib.api.abstract_client import AbstractClient
from lib.logger import logger
from lib.util import get_dict_value, re_pick


class GiteeClient(AbstractClient):
    '''gitee api'''
    '''
    https://gitee.com/api/v5/swagger#/postV5ReposOwnerRepoPulls
    '''

    def __init__(self, http, token, url):
        super().__init__(http, token, url)
        self.api_root = "https://gitee.com/api/v5"

    def post_pull_request(self, title, body, head_branch, base_branch):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls"
        res = self.http.post(api, data={
            "access_token": self.token,
            "title": title,
            "body": body,
            "head": f"{self.owner}:{head_branch}",
            "base": base_branch
        }, res_is_standard=False, res_is_json=True)
        return res

    def query_pull_request(self, head_branch, base_branch, state='open'):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls?access_token={self.token}&head={self.owner}:{head_branch}&base={base_branch}&state={state}"
        res = self.http.get(api, res_is_standard=False, res_is_json=True)
        if len(res) > 0:
            return res[0]
        return None

    def get_pull_request_detail(self, pull_id):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}?access_token={self.token}"
        res = self.http.get(api, res_is_standard=False, res_is_json=True)
        return res

    def post_merge(self, pull_id, detail):
        if detail['assignees_number'] > 0:
            self.post_review(pull_id)
        if detail['testers_number'] > 0:
            self.post_test(pull_id)

        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}/merge"
        self.http.put(api, data={
            "access_token": self.token
        }, res_is_standard=False, res_is_json=True)

    def post_review(self, pull_id):
        logger.info("force approve review")
        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}/review"
        self.http.post(api, data={
            "access_token": self.token,
            "force": True
        }, res_is_standard=False, res_is_json=False)

    def post_test(self, pull_id):
        logger.info("force approve test")
        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}/test"
        self.http.post(api, data={
            "access_token": self.token,
            "force": True
        }, res_is_standard=False, res_is_json=False)
