import datetime
import json
import os
import shutil
import time

import git

from lib.api.index import api_clients
from lib.http import Http
from lib.logger import logger
from lib.model.config import Config
from lib.model.sync import SyncTask
from lib.util import shell, get_dict_value, check_need_push, set_dict_value, is_blank_dir
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


def text_center(text: str, length=40):
    return text.center(length, '-')


def sync_func(task: SyncTask, src_dir, target_dir):
    if task.copy_script is None or task.copy_script.strip() == '':
        shutil.copytree(src_dir, target_dir)
    else:
        exec(task.copy_script)


class SyncHandler:

    def __init__(self, root, config):
        self.root = root
        self.config: Config = config
        self.status = read_status(root)
        self.conf_repo = config.repo
        self.conf_options = config.options
        self.conf_repo_root = self.conf_options.repo_root

        proxy_fix = self.conf_options.proxy_fix
        use_system_proxy = self.conf_options.use_system_proxy
        self.http = Http(use_system_proxy=use_system_proxy, proxy_fix=proxy_fix)

        self.repo = git.Repo.init(path=root)

    def handle(self):
        """
        处理 sync 命令
        """
        logger.info(text_center("sync start"))
        config = self.config
        os.chdir(self.root)
        # 初始化一下子项目，以防万一
        shell(f"git submodule update --init --recursive --progress")
        sms = self.repo.submodules
        if not sms:
            logger.info("Not initialized yet, please execute the [trident init] command first")
            return

        conf_sync_map = config.sync

        try:
            for key in conf_sync_map:
                conf_sync: SyncTask = conf_sync_map[key]
                # 执行同步任务
                task_executor = TaskExecutor(self.root, self.config, self.status, sms, self.http, conf_sync)
                task_executor.do_task()

            self.config.status.success = True

            # 所有任务已完成
            # 提交同步仓库的变更
            self.commit_cur_repo()
            self.repo.close()
        finally:
            self.render_result(conf_sync_map)
            logger.info(text_center("sync end"))

    def render_result(self, conf_sync_map):
        def right(target: str, res: bool, label_length=8):
            return f"{target.rjust(label_length, ' ')}:{'✅' if res else '🚫'}"

        def fill(string: str):
            return string.ljust(15, " ")

        cs = self.config.status
        result = text_center(right('result', cs.success, 0))
        for key in conf_sync_map:
            t: SyncTask = conf_sync_map[key]
            s = t.status
            task_result = f"\n 🏹 {fill(t.key)} --> {right('success', s.success)} {right('copy', s.copy)} {right('change', s.change)} {right('commit', s.commit)} {right('push', s.push)} {right('pr', s.pr)} {right('merge', s.merge)}"
            result += task_result
        result += f"\n 🔱 {fill('sync_work_repo')} --> {right('change', cs.change)} {right('commit', cs.commit)} {right('push', cs.push)} "
        # 输出结果
        logger.info(result)

    def commit_cur_repo(self):
        os.chdir(self.root)
        repo = self.repo
        shell("git add .")
        count = get_git_modify_file_count()
        if count <= 0:
            logger.info("No modification, no need to submit")
        else:
            self.config.status.change = True
            now = datetime.datetime.now()
            time.sleep(1)
            shell(f'git commit -m "🔱: sync all task at {now} [trident-sync]"')
            self.config.status.commit = True
            # shell(f"git push")
            if self.conf_options.push:
                need_push = check_need_push(repo, repo.head)
                if need_push is None:
                    logger.warning(
                        "Skip push，The remote address is not set for the current repository. Use the [trident remote <repo_url>] command to set the remote address of the repository and save the synchronization progress")
                elif need_push is True:
                    shell(f"git push")
                    self.config.status.push = True


class TaskExecutor:
    def __init__(self, root, config: Config, status: dict, sms, http, conf_sync: SyncTask):
        self.key = conf_sync.key
        self.root = root
        self.conf_sync = conf_sync
        self.sms = sms
        self.conf_repo = config.repo
        self.conf_src = conf_sync.src
        self.conf_target = conf_sync.target

        self.conf_options = config.options

        self.status = status
        self.http = http

        self.conf_src_repo = self.conf_src.repo_ref
        self.conf_target_repo = self.conf_target.repo_ref
        self.repo_src = sms[self.conf_src.repo].module()
        self.repo_target = sms[self.conf_target.repo].module()

    def do_task(self):

        logger.info(text_center(f"【{self.key}】 task start"))
        time.sleep(0.2)

        # 同步任务开始
        # 更新源仓库代码
        self.pull_src_repo()
        # 当前目录切换到目标项目
        os.chdir(self.repo_target.working_dir)
        # 先强制切换回主分支
        force_checkout_main_branch(self.conf_target.repo_ref)
        # 创建同步分支，并checkout
        is_first = checkout_branch(self.repo_target, self.conf_target.branch)
        # 开始复制文件
        self.do_sync(is_first)
        # 提交代码
        self.do_commit()
        # push更新
        has_push = self.do_push()
        # 创建PR
        self.do_pull_request(has_push)
        # 切换回主分支
        force_checkout_main_branch(self.conf_target.repo_ref)

        logger.info(text_center(f"【{self.key}】 task complete"))
        self.conf_sync.status.success = True
        self.repo_src.close()
        self.repo_target.close()

    def pull_src_repo(self):
        logger.info(f"update src repo :{self.conf_src.repo_ref.url}")
        shell(f"cd {self.repo_src.working_dir} && git checkout {self.conf_src.repo_ref.branch} && git pull")
        logger.info(f"update submodule of src repo")
        shell(f"cd {self.repo_src.working_dir} && git submodule update --init --recursive --progress ")
        logger.info(f"update src repo success")

    def do_sync(self, is_first):
        dir_src_sync = f"{self.repo_src.working_dir}/{self.conf_src.dir}"
        dir_target_sync = f"{self.repo_target.working_dir}/{self.conf_target.dir}"
        logger.info(f"sync dir：{dir_src_sync}->{dir_target_sync}")
        # 检查源仓库目录是否有文件，如果没有文件，可能初始化仓库不正常
        src_is_blank = is_blank_dir(dir_src_sync)
        if src_is_blank:
            raise Exception(
                f"The src repo dir <{dir_src_sync}> is empty. It may not be fully initialized. Try to enter this directory and execute the [git pull] command")

        if is_first:
            # 第一次同步，目标目录必须为空
            target_is_blank = is_blank_dir(dir_target_sync)
            if not target_is_blank:
                logger.warning(
                    f"For the first time, the target repo dir <{dir_src_sync}> is not empty")
                logger.warning(
                    f"Please make sure that the dir is a copy of a version of the src repo, otherwise please change the directory!!")
                logger.warning(
                    f"If you are sure that the directory is a copy of the source repository, you can try configuring \
                    <sync.[task].target.allow_reset_to_root:true> and reruning [trident sync] command ,This will \
                    reset the sync_branch to first commit to see if an earlier version had the \
                    directory.")
                if not self.conf_target.allow_reset_to_root:
                    raise Exception(
                        f"the target repo dir <{dir_src_sync}> is not empty, and allow_reset_to_root is False")
                else:
                    logger.info(f"The allow_reset_to_root is True, Trying to reset the sync_branch to root commit")
                    root_hash = shell("git rev-list --max-parents=0 HEAD", get_out=True)
                    shell(f"git reset {root_hash.strip()}")
                    shell("git clean -df ")
                    # 再次检测目录是否为空
                    target_is_blank = is_blank_dir(dir_target_sync)
                    if not target_is_blank:
                        raise Exception(
                            f"The target repository directory <{dir_src_sync}> is still not empty, please change the directory")

        if os.path.exists(dir_target_sync):
            shutil.rmtree(dir_target_sync)
            time.sleep(0.2)

        sync_func(self.conf_sync, dir_src_sync, dir_target_sync)
        git_file = f"{dir_target_sync}/.git"
        if os.path.exists(git_file):
            os.unlink(git_file)
        logger.info(f"【{self.key}】 Copy completed, ready to submit : {self.conf_target.dir}")
        time.sleep(1)
        self.conf_sync.status.copy = True

    def do_commit(self):
        shell(f"git add .")
        time.sleep(1)
        count = get_git_modify_file_count()
        time.sleep(1)
        logger.info(f"modify count : {count}")
        key = self.key
        if count <= 0:
            logger.info(f"【{key}】 No change, no need to submit")
            return False
        else:
            self.conf_sync.status.change = True
            last_commit = get_dict_value(self.status, f"sync.{key}.last_commit_src")
            messsges = collection_commit_message(self.repo_src, self.conf_src.repo_ref.branch, last_commit)
            body = ""
            for msg in messsges:
                body += msg + "\n"
            now = datetime.datetime.now()
            message = f"🔱: [{key}] sync upgrade with {len(messsges)} commits [trident-sync] "
            # 提交更新
            shell(f'git commit -m "{message}" -m "{body}"')
            # repo_target.index.commit(f"sync {key} success [{now}]")
            logger.info(f"【{key}】 submit success")
            time.sleep(0.2)
            # 记录最后提交hash
            src_last_hash = self.repo_src.head.commit.hexsha
            target_last_hash = self.repo_target.head.commit.hexsha

            set_dict_value(self.status, f"sync.{key}.last_commit_src", src_last_hash)
            set_dict_value(self.status, f"sync.{key}.last_commit_target", target_last_hash)
            save_status(self.root, self.status)
            self.conf_sync.status.commit = True
            return True

    def do_push(self):
        if not self.conf_options.push:
            return False
        logger.info("Check if push is needed")
        # 检测是否需要push
        key = self.key
        need_push = check_need_push(self.repo_target, self.conf_target.branch)
        if need_push is False:
            logger.info("No commit to push")
            return False
        else:
            logger.info("need push")
            logger.info(f"【{key}】 pushing")
            shell(f'git push --set-upstream origin {self.conf_target.branch}')
            logger.info(f"【{key}】 push success")
            time.sleep(0.2)
            self.conf_sync.status.push = True
            return True

    def do_pull_request(self, has_push):
        key = self.key
        if not self.conf_options.pull_request:
            return False
        if not has_push:
            return False
        token = self.conf_target.repo_ref.token
        repo_type = self.conf_target.repo_ref.type
        auto_merge = self.conf_target_repo.auto_merge
        if not repo_type:
            logger.warning(f"[repo:{self.conf_target.repo}] type is not configured, Unable to create PR")
            return False
        if not token:
            logger.warning(f"[repo:{self.conf_target.repo}] token is not configured, Unable to create PR")
            return False
        else:
            client = api_clients[repo_type](self.http, token, self.conf_target.repo_ref.url)
            title = f"[{key}] sync upgrade [trident-sync]"
            body = f"{self.conf_src.repo}:{self.conf_src_repo.branch}:{self.conf_src.dir} -> {self.conf_target.repo}:\
                {self.conf_target_repo.branch}:{self.conf_target.dir} "
            logger.info(
                f"Ready to create PR, {self.conf_target.branch} -> {self.conf_target_repo.branch} , url:{self.conf_target_repo.url}")
            try:
                pull_id, merged = client.create_pull_request(title, body, self.conf_target.branch,
                                                             self.conf_target_repo.branch,
                                                             auto_merge=auto_merge)
                self.conf_sync.status.pr = True
                if merged:
                    self.conf_sync.status.merge = True
            except Exception as e:
                # logger.opt(exception=e).error("提交PR出错")
                logger.error(f"Error creating PR：{e}")
            time.sleep(0.2)
            return True
