from lib.api.gitea import GiteaClient
from lib.api.gitee import GiteeClient
from lib.api.github import GithubClient

api_clients = {
    "github": GithubClient,
    "gitee": GiteeClient,
    "gitea": GiteaClient
}
