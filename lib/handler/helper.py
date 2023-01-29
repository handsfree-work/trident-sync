import datetime
import os
import time

from git import Repo

from lib.logger import logger
from lib.model.config import RunStatus
from lib.util import shell, check_need_push
from lib.util_git import get_git_modify_file_count


def save_work_repo(repo: Repo, message, push=True, status: RunStatus = None):
    shell("git add .")
    if status is None:
        status = RunStatus()
    count = get_git_modify_file_count()
    if count <= 0:
        logger.info("No modification, no need to submit")
    else:
        status.change = True
        time.sleep(1)
        shell(f'git commit -m "{message}"')
        status.commit = True

    if push:
        need_push = check_need_push(repo, repo.active_branch)
        if need_push is None:
            logger.warning(
                "Skip push，The remote address is not set for the current repository")
            logger.warning(
                "Use the [trident remote --url=<repo_url>] command to set the remote address of the repository and save the synchronization progress")

        elif need_push is True:
            shell(f"git push")
            status.push = True
        else:
            logger.info("No need to push")
