import requests
from bs4 import BeautifulSoup as bs

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
}


def post(url: str, data: dict, params: dict):
    r = requests.post(url, params=params, data=data, headers=headers)
    return r.status_code, r.text


def get(url: str, params: dict):
    r = requests.get(url, params=params, headers=headers)
    return r.status_code, r.text


def get_json(url: str, params: dict):
    r = requests.get(url, params=params, headers=headers)
    return r.status_code, r.json()


def soupify(text):
    return bs(text, "lxml")


def innerHTML(html_tag):
    text = ""
    for c in html_tag.contents:
        text+=str(c)
    return text