# 启用PR

同步成功后，支持自动创建PR

要开启此功能需要给对应的 `target_repo` 配置 `token` 和 `type`

```yaml
repo:
  target:
    url: 'xxxx'
    path: 'xxxx'
    branch: 'xxxx'
    type: 'github'   # 远程仓库类型。可选值：[github / gitee / gitea ]
    token: "xxxxxxx" # 授权token，请根据下方说明创建
    auto_merge: true # PR没冲突时，是否自动合并
```

# token创建

## 1、 github token

从此处创建token: https://github.com/settings/tokens

如果是 `Fine-grained tokens (beta) `    
要注意如下几点：

1. 选择正确的 `Resource owner`
2. `Repository access`,要选择 `All repositories` 或者 `Only select repositories(选择特定仓库)`
3. `Repository permissions` 中的 `Contents ` `Pull requests` 都要选择`read and write`

如果是 `Personal access tokens (classic)`

1. 只需要勾选 `repo` 即可

## 2、 gitee token

从此处创建token    
https://gitee.com/profile/personal_access_tokens

token所属账号要求（如果账号本身就是`仓库拥有者`，可以无视）

1. 需要有对仓库具备审查和测试权限，前往仓库设置页面设置：（owner/repo替换成你的项目地址）
   https://gitee.com/<owner>/<repo>/settings#set_pr_assigner

2. 需要对仓库具有管理员权限，前往成员管理页面设置：
   https://gitee.com/handsfree-test/pr-test/team?type=masters

## 3、 gitea token

从管理AccessToken栏目中创建token （将your.gitea.host 替换成你的实际gitea地址）     
https://your.gitea.host/user/settings/applications

## 4、 gitlab token

暂未实现



