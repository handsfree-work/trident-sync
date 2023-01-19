from lib.api.abstract_client import AbstractClient


class GiteaClient(AbstractClient):
    '''gitea api'''
    '''
    http://gitea.baode.docmirror.cn/{repos}/{owner}
    
    https://try.gitea.io/api/swagger#/repository/repoMergePullRequest
    
    '''

    def __init__(self, http, token, url):
        super().__init__(http, token, url)
        self.api_root = f"{self.url_prefix}/api/v1"

    def post_pull_request(self, title, body, head_branch, base_branch):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls?access_token={self.token}"
        res = self.http.post(api, data={
            "title": title,
            "body": body,
            # "head": f"{self.owner}:{src_branch}",
            "head": f"{head_branch}",
            "base": base_branch
        }, res_is_standard=False, res_is_json=True)
        return res

    def query_pull_request(self, head_branch, base_branch, state='open'):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls?access_token={self.token}&head={head_branch}&base={base_branch}&state={state}"
        # api = f"{self.api_root}/repos/{self.repo_path}/pulls?access_token={self.token}&head={src_branch}&base={target_branch}&state=open"
        res = self.http.get(api, res_is_standard=False, res_is_json=True)
        if len(res) > 0:
            return res[0]
        return None

    def get_pull_request_detail(self, pull_id):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}?access_token={self.token}"
        res = self.http.get(api, res_is_standard=False, res_is_json=True)
        return res

    def post_merge(self, pull_id, detail):
        api = f"{self.api_root}/repos/{self.repo_path}/pulls/{pull_id}/merge?access_token={self.token}"
        self.http.post(api, data={
            "Do": 'merge'
        }, res_is_standard=False, res_is_json=False)
