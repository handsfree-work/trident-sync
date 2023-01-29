"""
异构仓库同步升级工具

Precondition:
    1. install git
Usage:
    trident init [-r ROOT] [-c CONFIG]
    trident sync [-r ROOT] [-c CONFIG] [-t TOKEN] [-i]
    trident remote [-r ROOT] [-u URL] [-f]
    trident version
    trident -h
Options:
    -h,--help           show help menu, 显示帮助菜单
    -c,--config=CONFIG  config file path, 配置文件  [default: sync.yaml]
    -r,--root=ROOT      root dir, 根目录  [default: .]
    -t,--token=TOKEN    PR token
    -u,--url=URL        remote git url, 远程地址
    -f,--force          force push, 强制推送
    -i,--init           init first, 同步前先初始化
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
from lib.version import get_version


def cli():
    """
    异构仓库同步升级工具入口
    """
    args = docopt(__doc__)

    version = get_version()

    print(f'''
 
                  ████████╗██████╗ ██╗██████╗ ███████╗███╗   ██╗████████╗  
                  ╚══██╔══╝██╔══██╗██║██╔══██╗██╔════╝████╗  ██║╚══██╔══╝  
                     ██║   ██████╔╝██║██║  ██║█████╗  ██╔██╗ ██║   ██║     
                     ██║   ██╔══██╗██║██║  ██║██╔══╝  ██║╚██╗██║   ██║     
                     ██║   ██║  ██║██║██████╔╝███████╗██║ ╚████║   ██║     
                     ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝     
                      https://github.com/handsfree-work/trident-sync       
                    Don't be stingy with your star ( 请不要吝啬你的star )
                       Copyright © 2023 greper@handsfree.work v{version}    
                                                  
        ''')
    root = get_root(args)
    if not os.path.exists(root):
        os.makedirs(root)

    arg_config = get_arg(args, '--config')
    config_dict = read_config(arg_config)

    os.chdir(root)
    if args['remote']:
        remote_url = args['--url']
        force = args['--force']
        RemoteHandler(root, remote_url=remote_url, force=force).handle()
        return

    token_from_args = get_arg(args, '--token')
    config = Config(config_dict)
    config.set_default_token(token_from_args)

    if args['init']:
        InitHandler(root, config).handle()
    elif args['sync']:
        init_first = get_arg(args, '--init')
        if init_first:
            logger.info("init first")
            InitHandler(root, config).handle()
        SyncHandler(root, config).handle()
    else:
        logger.info(__doc__)


def read_config(arg_config='./sync.yaml'):
    config_file = os.path.abspath(f"{arg_config}")
    f = open(config_file, 'r', encoding='utf-8')
    return yaml.load(f, Loader=yaml.FullLoader)


def get_root(args):
    root = get_arg(args, '--root')
    return os.path.abspath(root)


if __name__ == '__main__':
    cli()
