import shutil


# custom copy script
def copy(task, src_dir, target_dir):
    shutil.copytree(src_dir, target_dir)
