from lib.api.abstract_client import AbstractClient


class GithubClient(AbstractClient):
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

    def post_pull_request(self, title, body, head_branch, base_branch):
        """
        head_branch 来源分支
        base_branch 被合并分支
        """
        api = f"https://api.github.com/repos/{self.repo_path}/pulls"
        res = self.http.post(api, data={
            "title": title,
            "body": body,
            "head": f"{self.owner}:{head_branch}",
            "base": base_branch,
            "maintainer_can_modify": True
        }, headers=self.headers, res_is_standard=False, res_is_json=True)
        return res

    def query_pull_request(self, head_branch, base_branch, state='open'):
        api = f"https://api.github.com/repos/{self.repo_path}/pulls?head={self.owner}:{head_branch}&base={base_branch}&state={state}"
        res = self.http.get(api, headers=self.headers, res_is_standard=False, res_is_json=True)
        if len(res) > 0:
            return res[0]
        return None

    def get_pull_request_detail(self, pull_id):
        api = f"https://api.github.com/repos/{self.repo_path}/pulls/{pull_id}"
        res = self.http.get(api, headers=self.headers, res_is_standard=False, res_is_json=True)
        return res

    def post_merge(self, pull_id, detail):
        api = f"https://api.github.com/repos/{self.repo_path}/pulls/{pull_id}/merge"
        self.http.put(api, data={}, headers=self.headers, res_is_standard=False, res_is_json=True)
