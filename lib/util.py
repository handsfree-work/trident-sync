import os
import shutil
import stat
import subprocess as sp
import re
from lib.logger import logger


def re_pick(re_str, input_str, flags=0):
    # inputStr = "['{0: 203, 11: 1627438682 [2021-07-28 10:18:02],  12:36 [通过蓝牙更改错误密码锁定计数], 13: 770449129, 19: 3, 20: 0, 100: 2141634486}']"

    reg = re.compile(re_str, flags)  # 增加匹配效率的 S 多行匹配
    lists = re.findall(reg, str(input_str))
    if len(lists) > 0:
        return lists[0]
    return []


def get_dict_value(dict_target, key, def_value=None):
    arr = str.split(key, '.')
    value = None
    parent = dict_target
    for key in arr:
        if parent and key and key in parent:
            value = parent[key]
            parent = value
        else:
            value = None
    if value is None:
        value = def_value
    return value


def set_dict_value(dict_target: object, key: str, value: object) -> object:
    arr = str.split(key, '.')
    parent = dict_target
    last_key = arr[len(arr) - 1]
    for key in arr:
        if last_key == key:
            parent[key] = value
            return
        if key not in parent:
            parent[key] = {}
        parent = parent[key]


def shell(cmd, ignore_errors=False, get_out=False):
    logger.info(cmd)
    out = None
    if get_out:
        out = sp.PIPE

    p = sp.run(cmd, shell=True, encoding='utf-8', stdout=out)
    if p.returncode != 0 and not ignore_errors:
        logger.debug(p.stdout)
        logger.debug(p.stderr)
        raise Exception(p.stderr)
    if get_out and p.stdout:
        logger.debug(p.stdout)
    return p.stdout


def read_file(file_path):
    if not os.path.exists(file_path):
        return None
    fo = open(file_path, "r", encoding='utf-8')
    content = fo.read()
    fo.close()
    return content


def save_file(file_path, content):
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    fo = open(file_path, "w", encoding='utf-8')
    fo.write(content)
    fo.close()


def check_need_push(repo, branch):
    """
    检查是否需要push，hash相等返回false，hash不相等返回true，没有远程分支返回None
    :param repo:
    :param branch:
    :return:
    """
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


def merge_from_dict(obj, dic):
    for key in dic:
        setattr(obj, key, dic[key])


def rm_dir(root):
    def readonly_handler(func, path, exe_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(root, onerror=readonly_handler)


def get_arg(args, key):
    value = args[key]
    if isinstance(value, list):
        if len(value) > 0:
            value = value[0]
        else:
            return None
    return value


def is_blank_dir(root):
    """
    检查目录是否为空，如果目录不存在也返回True
    """
    if not os.path.exists(root):
        return True
    is_blank = True
    for file in os.listdir(root):
        if file == '.git':
            continue
        is_blank = False
        break
    return is_blank
