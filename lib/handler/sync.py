import datetime
import json
import os
import shutil
import time

import git

from lib.api.index import api_clients
from lib.http import Http
from lib.logger import logger
from lib.model.opts import Options
from lib.model.sync import SyncTask
from lib.util import shell, get_dict_value, check_need_push, set_dict_value
from lib.util_git import force_checkout_main_branch, checkout_branch, collection_commit_message, \
    get_git_modify_file_count


def read_status(root):
    file_path = f'{root}/status.json'
    if not os.path.exists(file_path):
        return {}
    fo = open(file_path, "r")
    config_str = fo.read()
    fo.close()
    if config_str is None:
        return {}
    try:
        return json.loads(config_str)
    except Exception as e:
        print(e)
        return {}


def save_status(root, status):
    # 创建配置文件
    file_path = f'{root}/status.json'
    # 写入配置文件
    config_str = json.dumps(status)
    fo = open(file_path, "w")
    fo.write(config_str)
    fo.close()
    return status


class SyncHandler:

    def __init__(self, root, config, token_from_args):
        self.root = root
        self.config = config
        self.status = read_status(root)
        self.conf_repo = config['repo']
        self.conf_options = Options(config['options'])
        self.conf_repo_root = self.conf_options.repo_root

        proxy_fix = self.conf_options.proxy_fix
        use_system_proxy = self.conf_options.use_system_proxy
        self.http = Http(use_system_proxy=use_system_proxy, proxy_fix=proxy_fix)

        self.repo = git.Repo.init(path=root)
        self.token_from_args = token_from_args

    def handle(self):
        """
        处理 sync 命令
        """
        config = self.config
        logger.info(f"--------------------- 开始同步 ---------------------∈")

        sms = self.repo.submodules
        if not sms:
            logger.info("还未初始化，请先执行初始化命令")
            return
        # 初始化一下子项目，以防万一
        shell(f"git submodule update --init --recursive --progress")

        if 'sync' not in config:
            raise Exception("sync必须配置")

        conf_sync_map = config['sync']

        for key in conf_sync_map:
            conf_sync = SyncTask(key, conf_sync_map[key], self.conf_repo)
            # 执行同步任务
            task_executor = TaskExecutor(conf_sync, self, sms)
            task_executor.do_task()

        # 所有任务已完成
        # 提交同步仓库的变更
        self.commit_cur_repo()

        logger.info(f"--------------------- 同步结束 ---------------------∈")

    def commit_cur_repo(self):
        os.chdir(self.root)
        repo = self.repo
        shell("git add .")
        count = get_git_modify_file_count()
        if count <= 0:
            logger.info("暂无修改，无需提交")
        else:
            now = datetime.datetime.now()
            time.sleep(1)
            shell(f'git commit -m "ψ: sync on {now}"')
            # shell(f"git push")
            if self.conf_options.push:
                need_push = check_need_push(repo, repo.head)
                if need_push is None:
                    logger.info(
                        "跳过push，当前仓库还未设置远程地址，请使用 trident remote <repo_url> 命令设置本仓库远程地址")
                elif need_push is True:
                    shell(f"git push")


class TaskExecutor:
    def __init__(self, conf_sync: SyncTask, parent: SyncHandler, sms):
        self.key = conf_sync.key
        self.root = parent.root
        self.parent = parent
        self.conf_sync = conf_sync
        self.sms = sms
        self.conf_repo = parent.conf_repo
        self.conf_src = conf_sync.src
        self.conf_target = conf_sync.target

        self.conf_options = parent.conf_options

        self.status = parent.status

        self.conf_src_repo = self.conf_src.repo_ref
        self.conf_target_repo = self.conf_target.repo_ref
        self.repo_src = sms[self.conf_src.repo].module()
        self.repo_target = sms[self.conf_target.repo].module()

    def do_task(self):

        logger.info(f"--------------------- 任务【{self.key}】开始 ---------------------∈")
        time.sleep(0.2)

        # 同步任务开始
        # 更新源仓库代码
        self.pull_src_repo()
        # 当前目录切换到目标项目
        os.chdir(self.repo_target.working_dir)
        # 先强制切换回主分支
        force_checkout_main_branch(self.conf_target.repo_ref)
        # 创建同步分支，并checkout
        checkout_branch(self.repo_target, self.conf_target.branch)
        # 开始复制文件
        self.do_sync()
        # 提交代码
        self.do_commit()
        # push更新
        has_push = self.do_push()
        # 创建PR
        self.do_pull_request(has_push)
        # TODO 通知用户？
        # 切换回主分支
        force_checkout_main_branch(self.conf_target.repo_ref)

        logger.info(f"--------------------- 任务【{self.key}】完成 ---------------------∈")

    def pull_src_repo(self):
        logger.info(f"更新源仓库:{self.conf_src.repo_ref.url}")
        shell(f"cd {self.repo_src.working_dir} && git checkout {self.conf_src.repo_ref.branch} && git pull")
        logger.info(f"更新源仓库成功")

    def do_sync(self, ):
        dir_src_sync = f"{self.repo_src.working_dir}/{self.conf_src.dir}"
        dir_target_sync = f"{self.repo_target.working_dir}/{self.conf_target.dir}"
        logger.info(f"同步目录：{dir_src_sync}->{dir_target_sync}")
        if os.path.exists(dir_target_sync):
            shutil.rmtree(dir_target_sync)
            time.sleep(0.2)
        shutil.copytree(dir_src_sync, dir_target_sync)
        git_file = f"{dir_target_sync}/.git"
        if os.path.exists(git_file):
            os.unlink(git_file)
        logger.info(f"{self.key} 复制完成,准备提交:{self.conf_target.dir}")
        time.sleep(1)

    def do_commit(self):
        shell(f"git add .")
        time.sleep(1)
        count = get_git_modify_file_count()
        time.sleep(1)
        print(f"modify count : {count}")
        key = self.key
        if count <= 0:
            logger.info(f"{key} 没有变化，无需提交")
            return False
        else:
            last_commit = get_dict_value(self.status, f"sync.{key}.last_commit_src")
            messsges = collection_commit_message(self.repo_src, self.conf_src.repo_ref.branch, last_commit)
            body = ""
            for msg in messsges:
                body += msg + "\n"
            now = datetime.datetime.now()
            message = f"ψ: [{key}] sync upgrade [by trident-sync] [{now}]"
            # 提交更新
            shell(f'git commit -m "{message}" -m "{body}"')
            # repo_target.index.commit(f"sync {key} success [{now}]")
            logger.info(f"{key} 提交成功")
            time.sleep(0.2)
            # 记录最后提交hash
            src_last_hash = self.repo_src.head.commit.hexsha
            target_last_hash = self.repo_target.head.commit.hexsha

            set_dict_value(self.status, f"sync.{key}.last_commit_src", src_last_hash)
            set_dict_value(self.status, f"sync.{key}.last_commit_target", target_last_hash)
            save_status(self.root, self.status)
            return True

    def do_push(self):
        if not self.conf_options.push:
            return False
        logger.info("检测是否需要push")
        # 检测是否需要push
        key = self.key
        need_push = check_need_push(self.repo_target, self.conf_target.branch)
        if need_push is False:
            logger.info("无需push")
            return False
        else:
            logger.info("需要push")
            logger.info(f"{key} pushing")
            shell(f'git push --set-upstream origin {self.conf_target.branch}')
            logger.info(f"{key} push success")
            time.sleep(0.2)
            return True

    def do_pull_request(self, has_push):
        key = self.key
        if self.conf_options.pull_request:
            return False
        if not has_push:
            return False
        token = self.conf_target.repo_ref.token
        repo_type = self.conf_target.repo_ref.type
        arg_token = self.parent.token_from_args
        auto_merge = self.parent.conf_options.auto_merge
        if not token and arg_token:
            token = arg_token
        if not repo_type or not token:
            logger.warning(f"{self.conf_target.repo} 未配置token 或 type，无法提交PR")
            return False
        else:
            client = api_clients[repo_type](self.parent.http, token, self.conf_target.repo_ref.url)
            title = f"[{key}] sync upgrade 【by trident-sync】"
            body = f"{self.conf_src.repo}:{self.conf_src_repo.branch}:{self.conf_src.dir} -> {self.conf_target.repo}:\
                {self.conf_target_repo.branch}:{self.conf_target.dir} "
            logger.info(
                f"准备提交pr, {self.conf_target.branch} -> {self.conf_target_repo.branch} , url:{self.conf_target_repo.url}")
            try:
                client.create_pull_request(title, body, self.conf_target.branch, self.conf_target_repo.branch,
                                           auto_merge=auto_merge)
            except Exception as e:
                # logger.opt(exception=e).error("提交PR出错")
                logger.error(f"提交PR出错：{e}")
            time.sleep(0.2)
            return True
