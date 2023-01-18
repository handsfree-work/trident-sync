import os.path

import git

from lib.api.abstract_client import pick_from_url
from lib.api.gitea import GiteaClient
from lib.api.gitee import GiteeClient
from lib.api.github import GithubClient
from lib.http import Http
from lib.logger import logger
from lib.util import shell, save_file, rm_dir

main_branch = 'main'
no_conflict_branch = 'no_conflict_branch'
conflict_branch = 'conflict_branch'


def prepare(origin_url):
    '''pr测试准备'''
    # 初始化git
    pr_test_git_dir = os.path.abspath("./tmp/pr_test_git")
    if os.path.exists(pr_test_git_dir):
        rm_dir(pr_test_git_dir)
    os.makedirs(pr_test_git_dir)
    os.chdir(pr_test_git_dir)

    shell("git init")
    readme = 'readme.md'
    readme_content = '1'
    save_file(readme, readme_content)
    shell("git add .")
    shell("git commit -m \"1\"")
    # origin = repo.create_remote("origin", url)
    shell(f"git remote add origin {origin_url}")

    # 创建基础分支
    repo = git.Repo.init(pr_test_git_dir)
    if repo.active_branch.name != main_branch:
        shell(f"git branch {main_branch}")
    shell(f"git checkout {main_branch}")
    shell(f"git push -f -u origin {main_branch}")

    # 创建特性分支1,追加一行,无冲突
    shell(f"git checkout {main_branch}")
    shell(f"git branch {no_conflict_branch}")
    shell(f"git checkout {no_conflict_branch}")
    readme = 'readme.md'
    readme_content = '1\n2'
    save_file(readme, readme_content)
    shell("git add .")
    shell("git commit -m \"no_conflict_branch\"")
    # origin = repo.create_remote("origin", url)
    shell(f"git push -f -u origin {no_conflict_branch}")

    # 创建特性分支2,冲突一行

    shell(f"git switch {main_branch}")
    shell(f"git branch {conflict_branch}")
    shell(f"git checkout {conflict_branch}")
    readme = 'readme.md'
    readme_content = '2'
    save_file(readme, readme_content)
    shell("git add .")
    shell("git commit -m \"conflict_branch\"")
    # origin = repo.create_remote("origin", url)
    shell(f"git push -f -u origin {conflict_branch}")

    logger.info('pr test prepare success')


def create_github_client(origin_url):
    http = Http()
    token = os.getenv('GITHUB_TOKEN')
    client = GithubClient(http, token, origin_url)
    return client


def create_gitee_client(origin_url):
    http = Http()
    token = os.getenv('GITEE_TOKEN')
    client = GiteeClient(http, token, origin_url)
    return client


def create_gitea_client(origin_url):
    http = Http()
    token = os.getenv('GITEA_TOKEN')
    client = GiteaClient(http, token, origin_url)
    return client


def test_pr_pick_git_url():
    origin_url = "https://github.com/handsfree-test/pr-test"
    res = pick_from_url(origin_url)
    assert res['owner'] == 'handsfree-test'
    assert res['repo'] == 'pr-test'

    res = pick_from_url(origin_url + "/")
    assert res['owner'] == 'handsfree-test'
    assert res['repo'] == 'pr-test'

    res = pick_from_url(origin_url + ".git")
    assert res['owner'] == 'handsfree-test'
    assert res['repo'] == 'pr-test'

    res = pick_from_url("http://docmirror.cn:6789/handsfree-test/pr-test.git")
    assert res['owner'] == 'handsfree-test'
    assert res['repo'] == 'pr-test'


def test_pr_github():
    origin_url = "https://github.com/handsfree-test/pr-test"
    prepare(origin_url)
    client = create_github_client(origin_url)
    title = "no_conflict branch pr"
    body = "no_conflict branch pr"
    src_branch = no_conflict_branch
    target_branch = main_branch
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=False)

    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=True)

    # 测试conflict pr
    title = "conflict branch pr"
    body = "conflict branch pr"
    src_branch = conflict_branch
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=True)


def test_pr_gitee():
    origin_url = "https://gitee.com/handsfree-test/pr-test"
    prepare(origin_url)
    client = create_gitee_client(origin_url)
    title = "no_conflict branch pr"
    body = "no_conflict branch pr"
    src_branch = no_conflict_branch
    target_branch = main_branch
    # 先不自动提交
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=False)

    # 自动提交
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=True)

    # 测试conflict pr
    title = "conflict branch pr"
    body = "conflict branch pr"
    src_branch = conflict_branch
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=True)


def test_pr_gitea():
    origin_url = "http://docmirror.cn:6789/handsfree-test/pr-test"
    prepare(origin_url)
    client = create_gitea_client(origin_url)
    title = "no_conflict branch pr"
    body = "no_conflict branch pr"
    src_branch = no_conflict_branch
    target_branch = main_branch
    # 先不自动提交
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=False)

    # 自动提交
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=True)

    # 测试conflict pr
    title = "conflict branch pr"
    body = "conflict branch pr"
    src_branch = conflict_branch
    client.create_pull_request(title, body, src_branch, target_branch, auto_merge=True)
