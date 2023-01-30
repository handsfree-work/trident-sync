import os

import git

from lib.logger import logger
from lib.util import shell


class RemoteHandler:

    def __init__(self, work_root, remote_url=None, force=False):
        self.work_root = work_root
        self.remote_url = remote_url
        self.force = force

    def handle(self):
        os.chdir(self.work_root)
        repo = git.Repo(path=self.work_root)
        cur_branch_name = repo.head.reference
        url = self.remote_url
        if 'origin' in repo.remotes:
            logger.info("The remote origin already exists and no url parameter is needed")
            shell("git pull")
        else:
            if not url:
                logger.info(
                    "Please use the [trident remote --url=<sync_work_repo_git_url>] command to set the remote address first")
                return
            else:
                shell(f"git remote add origin {url}")
                # origin = repo.create_remote("origin", url)
                logger.info('add remote origin success:' + url)
        force = ""
        if self.force:
            force = " -f "
        shell(f"git push -u {force} origin {cur_branch_name}")
        logger.info('push success')
