import os

import git

from lib.logger import logger
from lib.util import shell


class RemoteHandler:

    def __init__(self, root, remote_url=None):
        self.root = root
        self.remote_url = remote_url

    def handle(self):
        os.chdir(self.root)
        repo = git.Repo(path=self.root)
        cur_branch_name = repo.head.reference
        url = self.remote_url
        if 'origin' not in repo.remotes and not url:
            logger.info("请先通过 trident remote --url=<sync_git_url> 命令设置远程地址")
            return
        if url:
            if 'origin' in repo.remotes:
                logger.info("origin已经存在，无需传url")
            else:
                shell(f"git remote add origin {url}")
                # origin = repo.create_remote("origin", url)
                logger.info('关联远程地址成功:' + url)

        shell(f"git push -u origin {cur_branch_name}")
        logger.info('push 成功')
