"""
异构仓库同步升级工具

前置条件:
    1. 安装git
Usage:
    trident init [-r ROOT] [-c CONFIG]
    trident sync [-r ROOT] [-c CONFIG] [-t token]
    trident remote [-r ROOT] [-u URL]
    trident -h
Options:
    -h,--help           显示帮助菜单
    -c,--config=CONFIG  配置文件  [default: sync.yaml]
    -r,--root=ROOT      根目录  [default: .]
    -t,--token=TOKEN    PR token
    -u,--url=URL        远程地址
Example:
    trident init
    trident sync
    trident remote --url=https://github.com/handsfree-work/trident-test-sync
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

from lib.api.index import api_clients
from lib.handler.init import InitHandler
from lib.handler.sync import SyncHandler
from lib.http import Http
from lib.logger import logger
from lib.util import get_dict_value, set_dict_value, shell, get_git_modify_file_count, save_file


def cli():
    """
    异构仓库同步升级工具入口
    """
    args = docopt(__doc__)
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
                ψ                    请不要吝啬你的star哟                      ψ
                ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ
        ''')
    root = get_root(args)
    if not os.path.exists(root):
        os.mkdir(root)
    os.chdir(root)
    if args['remote']:
        handle_remote(root, args)
        return

    config = read_config(root, args)

    if args['init']:
        InitHandler(root, config).handle()
    elif args['sync']:
        SyncHandler(root, config, args).handle()
    else:
        logger.info(__doc__)


def handle_remote(root, args):
    repo = git.RepoRef(path=root)
    cur_branch_name = repo.head.reference
    url = args['--url']
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
