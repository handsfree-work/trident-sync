# 创建PR

同步成功后，支持自动创建PR

要开启此功能需要给对应的 target repo 配置 token 和 type

```yaml
repo:
  target:
    url: 'xxxx'
    path: 'xxxx'
    branch: 'xxxx'
    type: 'github'  # 远程仓库类型。可选值：[github / gitee / gitea / gitlab]
    token: "xxxxxxx" # 授权token，请根据下方说明创建
```

## 1、 github token
从此处创建token   
https://github.com/settings/tokens

## 2、 gitee token

从此处创建token    
https://gitee.com/profile/personal_access_tokens

## 3、 gitea token

https://your.gitea.host/user/settings/applications    （将your.gitea.host 替换成你的实际gitea地址）
从管理AccessToken栏目中创建token


## 4、 gitlab token

