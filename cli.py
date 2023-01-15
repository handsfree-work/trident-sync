"""
异构仓库同步升级工具

前置条件:
    1. 安装git
Usage:
    trident init [-r ROOT] [-c CONFIG]
    trident sync [-r ROOT] [-c CONFIG] [-t token]
    trident remote [-r ROOT] <url>
Options:
    -h,--help  显示帮助菜单
    -c,--config=CONFIG  配置文件  [default: sync.yaml]
    -r,--root=ROOT  根目录  [default: .]
    -t,--token=TOKEN PR token
Example:
    trident init -r . -c sync.yaml
    trident sync
    trident remote https://github.com/greper/trident-test
"""
import datetime
import logging
import shutil
import stat
import time

from docopt import docopt
import json
import os
import yaml
import git
from git import RemoteProgress

from lib.api.index import api_clients
from lib.http import Http
from lib.logger import logger
from lib.util import get_dict_value, set_dict_value, shell, get_git_modify_file_count, save_file


def cli():
    """
    异构仓库同步升级工具入口
    """
    print('''
            ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ
            ψ  ████████╗██████╗ ██╗██████╗ ███████╗███╗   ██╗████████╗  ψ
            ψ  ╚══██╔══╝██╔══██╗██║██╔══██╗██╔════╝████╗  ██║╚══██╔══╝  ψ
            ψ     ██║   ██████╔╝██║██║  ██║█████╗  ██╔██╗ ██║   ██║     ψ
            ψ     ██║   ██╔══██╗██║██║  ██║██╔══╝  ██║╚██╗██║   ██║     ψ
            ψ     ██║   ██║  ██║██║██████╔╝███████╗██║ ╚████║   ██║     ψ
            ψ     ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝     ψ 
            ψ      https://github.com/handsfree-work/trident-sync       ψ
            ψ              Don't be stingy with your star               ψ
            ψ                    请不要吝啬你的star哟                     ψ
            ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ
    ''')
    args = docopt(__doc__)
    root = get_root(args)
    config = read_config(root, args)

    if args['init']:
        handle_init(root, config)
    elif args['start']:
        handle_start(root, config, args)
    elif args['remote']:
        handle_remote(root, config, args)
    else:
        logger.info(__doc__)


class CloneProgressPrinter(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=""):
        print(
            op_code,
            cur_count,
            max_count,
            cur_count / (max_count or 100.0),
            message or "NO MESSAGE",
        )


def handle_init(root, config):
    """
    处理 init 命令
    """
    if not os.path.exists(root):
        os.mkdir(root)
    os.chdir(root)
    logger.info(f"即将在{root}目录初始化同步项目")
    logger.info(f"git init : {root}")
    shell('git init')
    repo = git.Repo(path=root)
    print(repo.heads)
    if len(repo.heads) == 0:
        save_ignore_file(root)
        shell("git add .")
        time.sleep(1)
        shell('git commit -m "sync init start"')
    logger.info("get submodules")
    sms = repo.iter_submodules()
    print(sms)
    conf_repos = config['repo']
    conf_options = config['options']
    conf_repo_root = conf_options['repo_root']
    for key in conf_repos:
        item = conf_repos[key]
        logger.info(f"add submodule:{item['url']}")
        path = f"{conf_repo_root}/{item['path']}"
        # repo.create_submodule(key, path, url=item['url'], branch=item['branch'])
        shell(f"git submodule add -b {item['branch']} --name {key} {item['url']} {path}")

    logger.info("更新所有仓库")

    shell(f"git submodule update --init --recursive --progress")
    repo.iter_submodules()
    repo.submodule_update(recursive=True)
    shell("git add .")
    time.sleep(1)
    shell('git commit -m "sync init success"')

    os.chdir(os.getcwd())
    logger.info("初始化完成")


def check_need_push(repo, branch):
    '''
    检查是否需要push，hash相等返回false，hash不相等返回true，没有远程分支返回None
    :param repo:
    :param branch:
    :return:
    '''
    local_hash = repo.head.commit.hexsha
    remote_hash = None
    refs = repo.refs
    logger.info(f"refs:{refs}")
    origin_key = f"origin/{branch}"
    if origin_key in refs:
        remote_hash = refs[origin_key].commit.hexsha
    else:
        return None

    logger.info(f"local_hash:{local_hash} -> remote_hash:{remote_hash} ")
    if local_hash == remote_hash:
        return False
    return True


def handle_start(root, config, args):
    """
    处理 start 命令
    """
    logger.info(f"--------------------- 开始同步 ---------------------∈")
    repo = git.Repo.init(path=root)
    sms = repo.submodules
    if not sms:
        logger.info("还未初始化，请先执行初始化命令")
        return

    conf_repo = config['repo']
    conf_options = config['options']
    conf_repo_root = conf_options['repo_root']
    conf_sync_map = config['sync']

    proxy_fix = get_dict_value(conf_options, 'proxy_fix')
    use_system_proxy = get_dict_value(conf_options, 'use_system_proxy')
    http = Http(use_system_proxy=use_system_proxy, proxy_fix=proxy_fix)

    status = read_status(root)
    for key in conf_sync_map:
        conf_sync = conf_sync_map[key]
        do_task(args, root, conf_options, conf_repo, conf_sync, key, sms, status, http)

    # 所有任务已完成
    # 当前目录切换回主目录
    os.chdir(root)
    # 提交变更
    shell("git add .")
    count = get_git_modify_file_count()
    if count <= 0:
        logger.info("暂无修改，无需提交")
    else:
        now = datetime.datetime.now()
        time.sleep(1)
        shell(f'git commit -m "sync on {now}"')
        # shell(f"git push")
        if conf_options['push']:
            need_push = check_need_push(repo, repo.head)
            if need_push is None:
                logger.info("跳过push，当前仓库还未设置远程地址，请使用 trident remote <repo_url> 命令设置本仓库远程地址")
            elif need_push is True:
                shell(f"git push")
    logger.info(f"--------------------- 同步结束 ---------------------∈")


def do_task(args, root, conf_options, conf_repo, conf_sync, key, sms, status, http):
    logger.info(f"--------------------- 任务【{key}】开始 ---------------------∈")
    time.sleep(0.2)
    conf_src = conf_sync['src']
    conf_target = conf_sync['target']
    conf_src_repo = conf_repo[conf_src['repo']]
    conf_target_repo = conf_repo[conf_target['repo']]
    repo_src = sms[conf_src['repo']].module()
    repo_target = sms[conf_target['repo']].module()

    def pull_src_repo():
        logger.info(f"更新源仓库:{conf_src_repo['url']}")
        shell(f"cd {repo_src.working_dir} && git pull")
        logger.info(f"更新源仓库成功")

    def back_to_main_branch():
        # 切换回主分支
        shell(f"git checkout -f {conf_target_repo['branch']}")
        time.sleep(1)

    def create_and_checkout(cur_rep, branch):
        logger.info(f"checkout同步分支：{branch}")
        if branch not in cur_rep.heads:
            shell(f"git branch {branch}")
            time.sleep(1)
        shell(f"git checkout {branch}")
        time.sleep(1)

    def do_sync():
        dir_src_sync = f"{repo_src.working_dir}/{conf_src['dir']}"
        dir_target_sync = f"{repo_target.working_dir}/{conf_target['dir']}"
        logger.info(f"同步目录：{dir_src_sync}->{dir_target_sync}")
        if os.path.exists(dir_target_sync):
            shutil.rmtree(dir_target_sync)
            time.sleep(0.2)
        shutil.copytree(dir_src_sync, dir_target_sync)
        git_file = f"{dir_target_sync}/.git"
        if os.path.exists(git_file):
            os.unlink(git_file)
        logger.info(f"{key} 复制完成,准备提交:{conf_target['dir']}")
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

    def do_commit():
        shell(f"git add .")
        time.sleep(1)
        count = get_git_modify_file_count()
        time.sleep(1)
        print(f"modify count : {count}")

        if count <= 0:
            logger.info(f"{key} 没有变化，无需提交")
            return False
        else:
            last_commit = get_dict_value(status, f"sync.{key}.last_commit_src")
            messsges = collection_commit_message(repo_src, conf_src_repo['branch'], last_commit)
            body = ""
            for msg in messsges:
                body += msg + "\n"
            now = datetime.datetime.now()
            message = f"sync: [{key}] sync upgrade [{now}] 【by trident-sync】"
            # 提交更新
            shell(f'git commit -m "{message}" -m "{body}"')
            # repo_target.index.commit(f"sync {key} success [{now}]")
            logger.info(f"{key} 提交成功")
            time.sleep(0.2)
            # 记录最后提交hash
            src_last_hash = repo_src.head.commit.hexsha
            target_last_hash = repo_target.head.commit.hexsha

            set_dict_value(status, f"sync.{key}.last_commit_src", src_last_hash)
            set_dict_value(status, f"sync.{key}.last_commit_target", target_last_hash)
            save_status(root, status)
            return True

    def do_push():
        if not get_dict_value(conf_options, 'push'):
            return False
        logger.info("检测是否需要push")
        # 检测是否需要push

        need_push = check_need_push(repo_target, conf_target['branch'])
        if need_push is False:
            logger.info("无需push")
            return False
        else:
            logger.info("需要push")
            logger.info(f"{key} pushing")
            shell(f'git push --set-upstream origin {conf_target["branch"]}')
            logger.info(f"{key} push success")
            time.sleep(0.2)
            return True

    def do_pull_request(has_push):
        if not get_dict_value(conf_options, 'pr'):
            return False
        # if not has_push:
        #     return False
        token = get_dict_value(conf_target_repo, 'token')
        repo_type = get_dict_value(conf_target_repo, 'type')
        arg_token = get_arg(args, '--token')
        if not token and arg_token:
            token = arg_token
        if not repo_type or not token:
            logger.warning(f"{conf_target['repo']} 未配置token 或 type，无法提交PR")
            return False
        else:
            client = api_clients[repo_type](http, token, conf_target_repo['url'])
            title = f"[{key}] sync upgrade 【by trident-sync】"
            body = f""
            logger.info(
                f"准备提交pr, {conf_target['branch']} -> {conf_target_repo['branch']} , url:{conf_target_repo['url']}")
            try:
                client.create_pull_request(title, body, conf_target['branch'], conf_target_repo['branch'])
            except Exception as e:
                # logger.opt(exception=e).error("提交PR出错")
                logger.error(f"提交PR出错：{e}")
            time.sleep(0.2)
            return True

    # 同步任务开始
    # 更新源仓库代码
    pull_src_repo()
    # 当前目录切换到目标项目
    os.chdir(repo_target.working_dir)
    # 先强制切换回主分支
    back_to_main_branch()
    # 创建同步分支，并checkout
    create_and_checkout(repo_target, conf_target['branch'])
    # 开始复制文件
    do_sync()
    # 提交代码
    do_commit()
    # push更新
    has_push = do_push()
    # 创建PR
    do_pull_request(has_push)
    # TODO 通知用户？
    # 切换回主分支
    back_to_main_branch()
    logger.info(f"--------------------- 任务【{key}】完成 ---------------------∈")


def handle_remote(root, config, args):
    url = args['<url>']
    if not url:
        shell(f"git remote add origin {url}")
        # origin = repo.create_remote("origin", url)
        logger.info('关联远程地址成功:' + url)

    shell(f"git push")
    logger.info('push 成功')


def readonly_handler(func, path, execinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)


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


def save_ignore_file(root):
    ignore_file = f"{root}/.gitignore"
    ignore = '''
.idea
.vscode
.git
__pycache__
'''
    save_file(ignore_file, ignore)


def read_config(root, args):
    arg_config = get_arg(args, '--config')
    config_file = f"{root}/{arg_config}"
    f = open(config_file, 'r', encoding='utf-8')
    return yaml.load(f, Loader=yaml.FullLoader)


def get_root(args):
    root = get_arg(args, '--root')
    return f"{os.getcwd()}/{root}"


def get_arg(args, key):
    value = args[key]
    if isinstance(value, list):
        value = value[0]
    return value


if __name__ == '__main__':
    cli()
