import os.path
import shutil

from cli import read_config
from lib.handler.init import InitHandler
from lib.handler.remote import RemoteHandler
from lib.handler.sync import SyncHandler
from lib.logger import logger
from lib.model.config import Config
from lib.model.repo import RepoConf
from lib.util import rm_dir, shell, save_file, read_file

cur_root = os.path.abspath(os.path.curdir)
print(cur_root)
tmp = os.path.abspath("./tmp/sync")
work_root = f"{tmp}/sync-work-repo"
dir_repos = f"{tmp}/original"
key_sub_repo = 'sync-src-submodule'
sub_git_url = f"https://gitee.com/handsfree-test/{key_sub_repo}"
save_git_url = f"https://gitee.com/handsfree-test/sync-work-repo"

sub_main_branch = "main"
dir_sub_repo = f"{dir_repos}/{key_sub_repo}"
readme_file = './readme.md'
key_src_repo = "sync-src"
key_target_repo = "target"
dir_src_repo = f"{dir_repos}/{key_src_repo}"
target_sync_branch = "test_sync"
sync_config_file_origin = f"{work_root}/../../../sync.yaml"
sync_config_file_save = f"{work_root}/sync.yaml"

config_dict = read_config(work_root, '../../../sync.yaml')
config = Config(config_dict)
config.set_default_token()


def mkdirs():
    if os.path.exists(tmp):
        rm_dir(tmp)
    os.makedirs(tmp)
    os.makedirs(work_root)

    os.makedirs(dir_repos)
    # 初始化 sub repo
    os.makedirs(dir_sub_repo)
    os.chdir(work_root)


def prepare():
    '''测试准备'''

    repo_src: RepoConf = config.repo[key_src_repo]
    mkdirs()
    os.chdir(dir_sub_repo)
    shell("git init")
    readme_content = 'submodule'
    save_file(readme_file, readme_content)
    shell("git add .")
    shell("git commit -m \"submodule init\"")
    shell(f"git remote add origin {sub_git_url}")
    shell(f"git push -f -u origin {sub_main_branch}")

    # 初始化 src repo
    os.makedirs(dir_src_repo)

    os.chdir(dir_src_repo)
    shell("git init")
    readme_content = 'src'
    save_file(readme_file, readme_content)
    shell("git add .")
    shell("git commit -m \"src init\"")
    shell(f"git remote add origin {repo_src.url}")

    # 添加submodule
    shell(f"git submodule add -b {sub_main_branch} --name {key_sub_repo} {sub_git_url} ./sub/{key_sub_repo}")
    shell("git add .")
    shell("git commit -m \"add sub\"")
    shell(f"git push -f -u origin {sub_main_branch}")

    # 初始化 target repo
    repo_target: RepoConf = config.repo[key_target_repo]
    dir_target_repo = f"{dir_repos}/{key_target_repo}"
    os.makedirs(dir_target_repo)

    os.chdir(dir_target_repo)
    shell("git init")
    readme_content = 'target'
    save_file(readme_file, readme_content)
    shell("git add .")
    shell("git commit -m \"target init\"")

    readme_content = 'src-copy'
    copy_readme_file = './package/sync-src/readme.md'
    save_file(copy_readme_file, readme_content)

    shell("git add .")
    shell("git commit -m \"sync-src-copy\"")

    shell(f"git remote add origin {repo_target.url}")
    shell(f"git push -f -u origin {repo_target.branch}")

    # 删除远程分支
    shell(f"git branch {target_sync_branch}")
    shell(f"git push -f -u origin {target_sync_branch}")
    shell(f"git push origin --delete {target_sync_branch}")

    shutil.copyfile(sync_config_file_origin, sync_config_file_save)
    logger.info('test prepare success')
    return config


def submodule_update():
    repo_src: RepoConf = config.repo[key_src_repo]
    submodule_dir = f"{dir_src_repo}/sub/{key_sub_repo}"
    os.chdir(submodule_dir)
    readme_content = "submodule v2"
    save_file(readme_file, readme_content)
    shell("git add .")
    shell("git commit -m \"sub update v2\"")
    shell(f"git push -f -u origin {sub_main_branch}")

    os.chdir(dir_src_repo)
    shell("git add .")
    shell("git commit -m \"src update v2\"")
    shell(f"git push -f -u origin {repo_src.branch}")


def test_prepare():
    prepare()


def test_init():
    InitHandler(work_root, config).handle()
    target_readme = f"{work_root}/repo/target/readme.md"
    target_readme_content = read_file(target_readme)
    assert target_readme_content == 'target'

    src_readme = f"{work_root}/repo/sync-src/readme.md"
    src_readme_content = read_file(src_readme)
    assert src_readme_content == 'src'

    sub_readme = f"{work_root}/repo/sync-src/sub/sync-src-submodule/readme.md"
    sub_readme_content = read_file(sub_readme)
    assert sub_readme_content == 'submodule'


def test_sync_first():
    # 测试第一次同步
    SyncHandler(work_root, config).handle()

    target_repo_dir = f"{work_root}/repo/target/"
    os.chdir(target_repo_dir)
    shell(f"git checkout {target_sync_branch}")

    readme = f"{target_repo_dir}/package/sync-src/readme.md"
    readme_content = read_file(readme)
    assert readme_content == 'src'

    readme = f"{target_repo_dir}/package/sync-src/sub/{key_sub_repo}/readme.md"
    readme_content = read_file(readme)
    assert readme_content == 'submodule'


def test_set_remote():
    os.chdir(work_root)
    RemoteHandler(work_root, remote_url=save_git_url, force=True).handle()


def test_submodule_update():
    # src的子模块有更新
    submodule_update()


# 测试重新init
def test_re_init():
    # 重复init测试
    InitHandler(work_root, config).handle()


def test_clone_save_repo():
    # 删除save仓库
    os.chdir(tmp)
    rm_dir(work_root)
    shell(f"git clone {save_git_url}")


def test_sync_second():
    # 测试第二次同步
    SyncHandler(work_root, config).handle()
    target_repo_dir = f"{work_root}/repo/target/"
    os.chdir(target_repo_dir)
    shell(f"git checkout {target_sync_branch}")

    readme = f"{target_repo_dir}/package/sync-src/readme.md"
    readme_content = read_file(readme)
    assert readme_content == 'src'

    readme = f"{target_repo_dir}/package/sync-src/sub/{key_sub_repo}/readme.md"
    readme_content = read_file(readme)
    assert readme_content == 'submodule v2'
