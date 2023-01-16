import time

from util_git import Repo

from lib.logger import logger
from lib.model.repo import RepoRef
from lib.util import shell


def force_checkout_main_branch(conf_repo_ref: RepoRef):
    # 切换回主分支
    shell(f"git checkout -f {conf_repo_ref.branch}")
    time.sleep(1)


def checkout_branch(repo: Repo.Base, branch: str):
    '''
    创建或更新分支，如果远程有，则从远程拉取
    '''
    # 看看远程是否有对应分支
    logger.info(f"checkout同步分支：{branch}")

    origin_key = f"origin/{branch}"
    origin_exists = False
    local_exists = False
    if origin_key in repo.refs:
        origin_exists = True

    if branch in repo.heads:
        local_exists = True

    if origin_exists and not local_exists:
        # 远程有，本地没有，从远程拉取
        shell(f"git branch {branch} --track origin/{branch}")
    elif not origin_exists and not local_exists:
        # 两边都没有，本地创建
        shell(f"git branch {branch}")
    elif origin_exists and local_exists:
        # 两边都有
        shell(f"git checkout {branch}")
        shell(f"git pull")
    time.sleep(1)
    shell(f"git checkout {branch}")
    time.sleep(1)


def collection_commit_message(repo, branch, last_commit=None, max_count=20):
    # 准备commit文本
    commits = repo.iter_commits(branch, max_count=max_count)
    messages = []
    more = "..."
    for item in commits:
        if item.hexsha == last_commit:
            more = ""
            break
        messages.append(item.message.strip())
    messages.append(more)
    return messages
