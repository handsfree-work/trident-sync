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
    print('lists={}'.format(lists))
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


def set_dict_value(dict_target: object, key: object, value: object) -> object:
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
        raise Exception(p.stderr)
    if get_out and p.stdout:
        print(p.stdout)
    return p.stdout


def read_file(file_path):
    if not os.path.exists(file_path):
        return None
    fo = open(file_path, "r")
    content = fo.read()
    fo.close()
    return content


def save_file(file_path, content):
    fo = open(file_path, "w")
    fo.write(content)
    fo.close()


def get_git_modify_file_count():
    ret = shell(f"git status", get_out=True)
    lines = ret.split("\n")
    file_list = []
    # 忽略的package列表

    count = 0
    for line in lines:
        start = line.find(':   ')
        if (start < 0):
            continue
        start += 1
        file = line[start:].strip()
        count += 1
    return count


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


def merge_from_dict(obj, dic):
    for key in dic:
        if key in obj:
            obj[key] = dic[key]


def rm_dir(root):
    def readonly_handler(func, path, exe_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(root, onerror=readonly_handler)
