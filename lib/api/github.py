import time

from lib.http import Http, HTTPException
from lib.logger import logger
from lib.util import get_dict_value


class GithubClient:
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
        self.token = token
        self.http = http
        self.url = url
        repo_path = self.url.strip().replace("https://github.com/", "").replace(".git", "")
        if repo_path.endswith("/"):
            repo_path = repo_path[0, len(repo_path) - 1]
        self.repo_path = repo_path
        logger.info(f'repo: {repo_path}')
        arr = repo_path.split("/")
        self.owner = arr[0]
        self.repo = arr[1]
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def create_pull_request(self, title, body, src_branch, target_branch):
        '''
        https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28

        curl \
          -X POST \
          -H "Accept: application/vnd.github+json" \
          -H "Authorization: Bearer <YOUR-TOKEN>"\
          -H "X-GitHub-Api-Version: 2022-11-28" \
          https://api.github.com/repos/OWNER/REPO/pulls \
          -d '{"title":"Amazing new feature","body":"Please pull these awesome changes in!","head":"octocat:new-feature","base":"master"}'
        '''

        pull_res = self.query_pull_request(src_branch, target_branch)
        if pull_res is None:
            pull_res = self.do_create_pull_request(title, body, src_branch, target_branch)
        self.check_mergeable(pull_res)
        return pull_res['number']

    def do_create_pull_request(self, title, body, src_branch, target_branch):
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

    def check_mergeable(self, res):
        pull_id = res['number']
        logger.info("5秒后检查是否自动合并")
        time.sleep(5)
        api = f"https://api.github.com/repos/{self.repo_path}/pulls/{pull_id}"
        res = self.http.get(api, headers=self.headers, res_is_standard=False, res_is_json=True)
        can_merge = self.can_auto_merge(res)
        if can_merge is True:
            logger.info("准备自动合并PR")
            # 准备自动合并
            api = f"https://api.github.com/repos/{self.repo_path}/pulls/{pull_id}/merge"
            self.http.put(api, data={}, headers=self.headers, res_is_standard=False, res_is_json=True)
            logger.info("自动合并成功")
