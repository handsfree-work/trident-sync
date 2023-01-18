# trident-sync 🔱 三叉戟同步

三叉戟同步，是一款异构项目同步升级工具，二次开发同步神器。

[中文](./readme.md) / [English](./readme-en.md)

## 1. 简介

当我们的项目内部使用了其他模版项目进行二次开发，那么那个模版项目就永远停留在当时的版本，无法方便的更新。

本项目可以自动获取变更并合并到你的项目仓库，让集成的模版项目持续升级。

本项目支持各类异构项目的同步升级

* `多个模版项目` 同步到 `你项目的多个目录`
* `模版项目的多个目录` 同步到 `你项目的多个目录`
* `你项目的多个目录` 同步到 `多个模版项目`
* `你项目的多个目录` 同步到 `模版项目的多个目录`

## 2. 缘起

我有一个 [certd](https://github.com/certd/certd) 项目，这是一个自动更新ssl证书的工具，但这不是重点。     
重点是它一开始只是一个独立的命令行工具。    
目录结构如下：

```
src
| --packages
    | --core           //实现申请证书的核心
    | --plugins        //一些任务插件，部署证书到远程服务器、云服务之上。

```

某一天我想开发v2版本，把它升级成一个带后台和界面的web项目。      
恰好我找到了两个模版项目(其实也是我写的🤭),可以帮我快速实现以上需求。

* [fs-admin-antdv](https://github.com/fast-crud/fs-admin-antdv)  （前端admin模版）
* [fs-server-js](https://github.com/fast-crud/fs-server-js)  （服务端）

我把这两个项目复制到了`certd`项目中,进行二次开发。     
此时`certd`项目目录结构变成如下：

```
src
| --packages
    | --core
    | --plugins
    | --ui
        | --certd-client   //这是fs-admin-antdv的副本
        | --certd-server   //这是fs-server-js的副本
```

为了使`certd-client`和`certd-server`能够随时同步`模版项目`的更新       
我将使用本项目`trident-sync`来自动帮我升级。

<p align="center">
<img src="./doc/images/trident.png" height="400"/>
<p align="center">像不像个三叉戟🔱？</p>
<p>

## 3. 原理

初始化（init）：

1. clone源仓库（src）和目标仓库（target）
2. 给目标仓库创建并切换到同步分支（sync_branch）
3. 将源仓库内的文件复制到目标仓库对应的目录，然后commit、push
4. 此时目标仓库内的sync_branch分支拥有源仓库的副本

同步（sync）：

1. 当源仓库有变更时、拉取源仓库更新
3. 删除目标仓库对应的目录，复制源仓库所有文件到目标仓库对应的目录
4. 此时`git add . && git commit` 提交的就是源仓库有变更的那部分内容
5. 然后创建`target.sync_branch` -> `target.main`的`PR`
6. 处理`PR`，合并到开发主分支，升级完成

![](./doc/images/desc.png)

> 没有冲突的话，同步过程可以全部自动化。    
> 解决冲突是唯一需要手动的部分。

## 4. 快速开始

### 4.1 准备工作

* 安装 [python (3.8+)](https://www.python.org/downloads/)
* 准备你的项目和要同步的模版项目仓库地址和分支
* 准备一个全新的git仓库地址，用来保存同步状态

```shell
# 安装本工具
pip install trident-sync --upgrade
# 创建一个同步目录，用来进行同步操作,你可以任意命名
mkdir project-sync
# 进入目录
cd project-sync
```

### 4.2 编写`sync.yaml`文件

下载 [sync.yaml模版](https://raw.githubusercontent.com/handsfree-work/trident-sync/main/sync.yaml)
文件保存到`project-sync`目录

根据其中的注释修改成你的配置

### 4.3 初始化

此命令会初始化一个同步仓库    
然后将`sync.yaml`中配置的多个`repo` 添加为`submodule`

```shell
# 执行初始化操作
trident init 
# 或者带上远程仓库地址，可以将同步状态记录下来，换台电脑也可以继续同步，无需重复初始化
trident init --url=<save_git_url>
```

> 1. 只需运行一次即可，除非你添加了新的`repo`    
> 2. `<save_git_url>` 必须是一个git空仓库


### 4.4 进行同步

将根据`sync.yaml`中`sync`配置的同步任务进行同步更新，并提交PR，等你有空时处理有冲突的PR即可

```shell
# 以后你只需要定时运行这个命令，即可保持同步升级
trident sync 
```

> 注意：不要在同步分支内写你自己的任何代码

### 4.5 [可选] 保存 project-sync

将`project-sync`提交到你的远程服务器，防止更换电脑丢失同步进度

```shell
# 给同步仓库设置远程地址，并push
trident remote --url=<project-sync_git_url> 
```

### 4.5 [可选] 定时运行

你可以将 `<project-sync>` 这个远程仓库和 `trident sync` 命令配置到任何`CI/DI`工具（例如jenkins、github
action、drone等）自动定时同步

### 4.6. 合并分支

同步完之后，将会有三种情况：

* 启用PR： [如何启用PR？](#启用PR)
    * 无冲突：自动创建PR，然后自动合并，你无需任何操作
    * 有冲突：自动创建PR，然后需要[手动处理PR](#处理PR)
* 未启用PR：
    * 你需要 [手动合并](#手动合并)

#### 启用PR

要启用PR，你需要如下配置

```yaml
repo:
  target:
    token: xxxx      # 创建PR的token
    type: github     # upstream类型，支持[ github | gitee | gitea ]
    auto_merge: true   # 是否自动合并

```

[token如何获取？](./doc/pr.md)

#### 处理PR

当PR有冲突时，就需要手动处理冲突，才能合并进入主分支

* 其中 `github` `gitee`支持在web页面直接手动解决冲突
* `gitea`需要线下解决，此时你仍然需要 [手动合并](#手动合并)

#### 手动合并

一般出现冲突了，都建议在IDE上手动进行合并

1. 关闭PR（没有PR的话，请无视）
2. 本地更新所有分支
3. 通过IDE进行分支merge操作（rebase也行，用你平常熟悉的合并分支操作）

```
target:<sync_branch> -------->  target:<main_branch>
    同步分支            merge         开发主分支
```

#### 避免冲突建议

我们应该尽量避免冲突，请实际开发中遵循以下原则：

1. 尽量不删除、不移动源项目的目录和文件（否则容易造成意想不到的难以解决的冲突）
2. 尽量少在源项目的文件上进行修改（可以改，但尽量少）
3. 新功能和新特性应该写在自己建立的新目录和新文件中

总结就是六个字： 不删、少改、多加。

## 6. 其他问题：

### 5.1 为何不fork模版项目，通过submodule来管理

这是我最初采用的方法，确实可以通过set-upstream,然后进行合并来进行同步升级。        
但管理众多的submodule仍然是一件费力且很容易出错的事情，比如：

* 想要采用git-flow模式，就得频繁切换所有的submodule的分支
* 想要管控main分支的提交权限，多个submodule相当繁琐
* lerna不支持submodule模块的发布

