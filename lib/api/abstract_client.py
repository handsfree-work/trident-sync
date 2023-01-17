import time
from abc import abstractmethod

from lib.logger import logger
from lib.util import re_pick


def pick_from_url(git_url):
    re_str = "(http[s]?)://([^/]+)/([^/]+)/([^/\\.]+)"
    res = re_pick(re_str, git_url)
    if len(res) < 4:
        raise Exception(f"异常的git_url: {git_url}")
    return {
        'protocol': res[0],
        'host': res[1],
        'owner': res[2],
        'repo': res[3],
    }


class AbstractClient:
    '''repo api'''
    token = 'token'
    http = None
    url = None
    repo_path = None
    owner = None
    repo = None
    api_root = None

    def __init__(self, http, token, url):
        self.token = token
        self.http = http
        self.url = url
        res = pick_from_url(url)
        self.owner = res['owner']
        self.repo = res['repo']
        self.url_prefix = f"{res['protocol']}://{res['host']}"
        self.repo_path = f"{self.owner}/{self.repo}"

    def create_pull_request(self, title, body, src_branch, target_branch, auto_merge=True):
        '''
        https://try.gitea.io/api/swagger#/repository/repoCreatePullRequest

         curl -X 'POST' \
          'http://gitea.baode.docmirror.cn/api/v1/repos/{owner}/{repo}/pulls?access_token=1a5461e976c423068cc7677e608681b3d992eefe' \
          -H 'accept: application/json'
        '''

        pull_res = self.query_pull_request(src_branch, target_branch)
        if pull_res is None:
            pull_res = self.post_pull_request(title, body, src_branch, target_branch)
        pull_id = pull_res['number']
        if auto_merge:
            self.auto_merge(pull_id)
        return pull_id

    def can_auto_merge(self, res):
        if 'mergeable' not in res:
            logger.warning("状态未知，请手动合并PR")
            return None
        mergeable = res['mergeable']
        if mergeable is True:
            return True
        if mergeable is False:
            logger.warning("可能有冲突，请手动合并PR")
            return False
        logger.warning("状态未知，请手动合并PR")
        return None

    def auto_merge(self, pull_id):
        logger.info("5秒后检查是否自动合并")
        time.sleep(5)
        res = self.get_pull_request_detail(pull_id)
        can_merge = self.can_auto_merge(res)
        if can_merge is True:
            logger.info("准备自动合并PR")
            # 准备自动合并
            self.post_merge(pull_id, res)
            logger.info("自动合并成功")

    @abstractmethod
    def post_pull_request(self, title, body, src_branch, target_branch):
        pass

    @abstractmethod
    def query_pull_request(self, src_branch, target_branch):
        pass

    @abstractmethod
    def get_pull_request_detail(self, pull_id):
        pass

    @abstractmethod
    def post_merge(self, pull_id, detail):
        pass