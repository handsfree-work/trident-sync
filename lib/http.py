import json

import requests
import urllib

from lib.logger import logger


class HttpException(Exception):
    # 自定义异常类型的初始化
    def __init__(self, msg, code, data):
        self.msg = msg
        self.code = code
        self.data = data

    # 返回异常类对象的说明信息
    def __str__(self):
        return self.msg


def standard_res_handle(res):
    if res['code'] == 0:
        return res['data']
    raise Exception(res['msg'], res['code'])


class Http:
    def __init__(self, use_system_proxy=True, proxy_fix=True):
        self.proxies = {'http': None, 'https': None}
        if use_system_proxy:
            proxies = urllib.request.getproxies()
            if proxy_fix and "https" in proxies:
                https_proxy = proxies['https']
                if https_proxy.startswith('https://'):
                    proxies['https'] = https_proxy.replace("https://", "http://")
            self.proxies = proxies
        self.verify = True
        self.logger = logger

    def set_proxies(self, proxies):
        self.proxies = proxies

    def options(self, url, cookies=None, headers=None, **kwargs):
        self.logger.debug(f"http request[options] url:{url}")
        if headers is None:
            headers = {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        session = requests.Session()
        session.trust_env = False
        response = session.options(url, proxies=self.proxies, headers=headers, cookies=cookies, **kwargs)
        self.logger.debug("http response: " + response.text)
        return

    def post(self, url, data, res_is_json=True, res_is_standard=True, cookies=None, headers=None, **kwargs):
        self.logger.debug(f"http request[post] url:{url}")
        if headers is None:
            headers = {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        session = requests.Session()
        session.headers.clear()
        session.headers.update(headers)
        session.trust_env = False
        response = session.post(url, json=data, proxies=self.proxies, headers=headers, cookies=cookies,
                                verify=self.verify, **kwargs)
        self.logger.debug("http response: " + response.text)
        return self.res_handle(response, res_is_json, res_is_standard)

    def put(self, url, data, res_is_json=True, res_is_standard=True, cookies=None, headers=None, **kwargs):
        self.logger.debug(f"http request[put] url:{url}")
        if headers is None:
            headers = {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        session = requests.Session()
        session.headers.clear()
        session.headers.update(headers)
        session.trust_env = False
        response = session.put(url, json=data, proxies=self.proxies, headers=headers, cookies=cookies,
                               verify=self.verify, **kwargs)
        self.logger.debug("http response: " + response.text)
        return self.res_handle(response, res_is_json, res_is_standard)

    def get(self, url, headers=None, res_is_json=True, res_is_standard=True):
        self.logger.debug(f"http request[get] url:{url}")
        if headers is None:
            headers = {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, proxies=self.proxies, verify=self.verify, headers=headers)
        self.logger.debug("http response: " + response.text)
        return self.res_handle(response, res_is_json, res_is_standard)

    def download(self, url, save_path, on_progress=None):
        session = requests.Session()
        session.trust_env = False
        down_res = session.get(url=url, proxies=self.proxies, stream=True)
        chunk_size = 1024 * 1024
        downloaded = 0
        content_size = int(down_res.headers['content-length'])  # 内容体总大小
        with open(save_path, "wb") as file:
            for data in down_res.iter_content(chunk_size=chunk_size):
                file.write(data)
                downloaded += len(data)
                if on_progress is not None:
                    on_progress({
                        'total': content_size,
                        'downloaded': downloaded,
                        'status': 'downloading'
                    })
        if on_progress:
            on_progress({
                'total': content_size,
                'downloaded': downloaded,
                'status': 'finished'
            })

    def res_handle(self, response, res_is_json, res_is_standard):

        if response.status_code < 200 or response.status_code > 299:
            return self.error_handle(response)

        if res_is_json:
            res = response.json()
            if res_is_standard:
                return standard_res_handle(res)
            return res
        else:
            return response.text

    def error_handle(self, response):
        data = {}
        try:
            data = json.loads(response.text)
        except Exception as e:
            pass
        raise HttpException(f'请求错误：({response.status_code}):{response.text}', 1, data)
