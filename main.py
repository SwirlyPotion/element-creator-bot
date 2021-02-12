import PIL
import requests
import json
import methods
import token_handler as tkn


def get_url(url, files=''):
    if files:
        response = requests.post(url, files=files)
    else:
        response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


class Drawer:
    pass


class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_handler = requests.HTTPHandler()

    def get_updates(offset=None):
        method = methods.getUpdates(offset=offset)
        url = tkn.format_method(method)
        js = get_json_from_url(url)
        return js

    def recieve_message(self):
        assert False

    def parse_message(self):
        assert False

    def send_messsage(self):
        assert False

    def run(self):
        assert False
