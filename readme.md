# trident-sync 三叉戟同步

异构项目同步升级CLI工具

[中文](./readme.md) / [English](./readme-en.md)

## 1. 简介

当我们的monorepo项目内部使用了其他模版项目，那么那个模版项目就永远停留在当时的版本，无法方便的更新。

本项目可以自动获取更新并提交PR到你的monorepo仓库，让集成的模版项目保持最新版本。

本项目支持各类异构项目的同步升级

* `多个模版项目` 同步到 `你项目的多个目录`
* `模版项目的多个目录` 同步到 `你项目的多个目录`
* `你项目的多个目录` 同步到 `多个模版项目`
* `你项目的多个目录` 同步到 `模版项目的多个目录`


## 2. 实现原理

初始化：

1. clone源仓库（src）和目标仓库（target）
2. 给目标仓库创建并切换到同步分支（sync_branch）
3. 将源仓库内的文件复制到目标仓库对应的目录，然后commit、push
4. 此时目标仓库内的sync_branch分支拥有源仓库的副本

升级：

1. 当源仓库有变更时
2. 拉取源仓库更新
3. 删除目标仓库对应的目录，复制源仓库所有文件到目标仓库对应的目录
4. 此时`git add . && git commit` 提交的就是源仓库有变更的那部分内容
5. 然后创建`target.sync_branch` -> `target.main`的`PR`
6. 处理`PR`

![](./doc/images/desc.png)

## 3. 应用场景

例如：   
我有一个 [certd](https://github.com/certd/certd) 项目，它是一个自动更新ssl证书的工具，但这不是重点。     
重点是它一开始只是一个独立的命令行工具。   
我通过`yarn`的`workspace`功能将多个子模块放在一个仓库中管理       
它的目录结构如下：

```js
src
| --packages
| --core           //实现申请证书的核心
| --plugins        //一些任务插件，部署证书到远程服务器、云服务之上。

```

某一天我想开发v2版本，想把它升级成一个带后台和界面的web项目。      
恰好我找到了两个模版项目,可以帮我快速实现以上需求。

* [fs-admin-antdv](https://github.com/fast-crud/fs-admin-antdv)  （前端admin模版）
* [fs-server-js](https://github.com/fast-crud/fs-server-js)  （服务端）

这时`certd`项目目录结构将变成如下：

```js
src
| --packages
| --core
| --plugins
| --ui
| --certd - client   //这是fs-admin-antdv的副本
| --certd - server   //这是fs-server-js的副本
```

为了使`certd-client`和`certd-server`能够随时同步`模版项目`的更新       
我将使用`trident-sync`来自动帮我升级。

<div style="text-align: center">
<img src="./doc/images/trident.png" height="400"/>
<div>像不像个三叉戟？</div>
</div>

## 4. 快速开始

### 4.1 准备工作

* 安装 [python](https://www.python.org/downloads/)
* 准备你的项目和要同步的模版项目仓库地址和分支

```shell
# 安装本工具
pip install trident-sync --upgrade
# 创建一个同步目录，用来进行同步操作,你可以任意命名
mkdir project-sync
# 进入目录
cd project-sync
```

### 4.2 编写`sync.yaml`文件

下载 [sync.yaml模版](https://raw.githubusercontent.com/handsfree-work/trident-sync/main/sync.yaml) 文件保存到`sync`目录

根据注释修改其中的配置

### 4.3 初始化

初始化会将sync初始化为一个git仓库    
然后将`sync.yaml`中配置的多个`repo` 添加为`submodule`

```shell
# 执行初始化操作
trident init 
```
> 注意：只需运行一次即可，除非你添加了新的`repo`

### 4.4 进行同步

将根据`sync.yaml`中`sync`配置的同步任务进行同步更新，并提交PR，当你有空时处理PR即可

```shell
# 以后你只需要定时运行这个命令，即可保持同步升级
trident sync 
```

### 4.5 [可选] 保存 project-sync

将`project-sync`提交到你的远程服务器，防止更换电脑丢失同步进度


```shell
# 给同步仓库设置远程地址，并push
trident remote --url=<project-sync_git_url> 
```

后续你可以在任意位置`clone`出`project-sync`之后，运行`trident sync`即可继续同步

> 注意：这个 `<project-sync_git_url>` 是一个全新的git仓库，用来保存同步进度的

### 4.5 [可选] 定时运行

你可以将 `<project-sync_git_url>` 这个远程仓库和 `trident sync` 命令配置到任何`CI/DI`工具（例如jenkins、github
action、drone等）自动定时同步

## 5. 其他问题：

### 5.1 为何不fork模版项目，通过submodule来管理

这是我最初采用的方法，确实可以通过set-upstream,然后进行合并来进行同步升级。        
但管理众多的submodule仍然是一件费力且很容易出错的事情，比如：     
* 想要采用git-flow模式，就得频繁切换所有的submodule的分支
* 想要管控main分支的提交权限，多个submodule相当繁琐
* lerna不支持submodule模块的发布

