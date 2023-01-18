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

import os

import yaml
from docopt import docopt

from lib.handler.init import InitHandler
from lib.handler.remote import RemoteHandler
from lib.handler.sync import SyncHandler
from lib.logger import logger
from lib.model.config import Config
from lib.util import get_arg


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
                ψ                    请不要吝啬你的star                        ψ
                ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ ψ
        ''')
    root = get_root(args)
    if not os.path.exists(root):
        os.mkdir(root)
    os.chdir(root)
    if args['remote']:
        remote_url = args['--url']
        RemoteHandler(root, remote_url=remote_url).handle()
        return

    arg_config = get_arg(args, '--config')
    config_dict = read_config(root, arg_config)

    token_from_args = get_arg(args, '--token')
    config = Config(config_dict)
    config.set_default_token(token_from_args)

    if args['init']:
        InitHandler(root, config).handle()
    elif args['sync']:
        SyncHandler(root, config).handle()
    else:
        logger.info(__doc__)


def read_config(root, arg_config):
    config_file = f"{root}/{arg_config}"
    f = open(config_file, 'r', encoding='utf-8')
    return yaml.load(f, Loader=yaml.FullLoader)


def get_root(args):
    root = get_arg(args, '--root')
    return f"{os.getcwd()}/{root}"


if __name__ == '__main__':
    cli()
