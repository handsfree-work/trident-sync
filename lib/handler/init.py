import os
import time

import git

from lib.logger import logger
from lib.model.config import Config
from lib.model.repo import RepoConf
from lib.util import shell, save_file
from lib.util_git import add_and_commit


class InitHandler:

    def __init__(self, root, config):
        self.root = root
        self.config = config

    def handle(self):
        """
        处理 init 命令
        """
        root = self.root
        config: Config = self.config
        logger.info(f"git init : {root}")
        os.chdir(root)
        shell('git init')
        repo = git.Repo(path=root)
        if len(repo.heads) == 0:
            self.save_ignore_file()
            shell("git add .")
            time.sleep(1)
            shell('git commit -m "🔱: sync init start [trident-sync]"')
        logger.info("get submodules")
        sms = repo.iter_submodules()
        conf_repos = config.repo
        conf_options = config.options
        conf_repo_root = conf_options.repo_root
        for key in conf_repos:
            added = False
            for module in sms:
                if key == module.name:
                    logger.info(f"{key} has been added to the submodule")
                    added = True
                    break
            if added:
                continue
            item: RepoConf = conf_repos[key]
            logger.info(f"add submodule:{item.url}")
            path = f"{conf_repo_root}/{item.path}"
            # repo.create_submodule(key, path, url=item['url'], branch=item['branch'])
            shell(f"git submodule add -b {item.branch} --name {key} {item.url} {path}")

        logger.info("Update all submodule")

        shell(f"git submodule update --init --recursive --progress")
        repo.iter_submodules()
        add_and_commit('🔱: sync init [trident-sync]')
        os.chdir(os.getcwd())
        logger.info("init success")
        repo.close()

    def save_ignore_file(self):
        ignore_file = f"{self.root}/.gitignore"
        ignore = '''
.idea
.vscode
.git
__pycache__
        '''
        save_file(ignore_file, ignore)
