import os
import subprocess as sp

from lib.logger import logger


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


def set_dict_value(dict_target, key, value):
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
