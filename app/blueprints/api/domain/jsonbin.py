import requests
from flask import current_app


def create(domains):
    print("creating")
    url = 'https://api.jsonbin.io/b'
    headers = {
      'Content-Type': 'application/json',
      'secret-key': current_app.config.get('JSONBIN_API_KEY')
    }
    data = domains

    req = requests.post(url, json=data, headers=headers)
    print(req.text)


def get():
    url = 'https://api.jsonbin.io/b/<BIN_ID>'
    headers = {'secret-key': current_app.config.get('JSONBIN_API_KEY')}

    req = requests.put(url, json=nil, headers=headers)
    print(req.text)


def update():
    url = 'https://api.jsonbin.io/b/<BIN_ID>'
    headers = {'Content-Type': 'application/json'}
    data = {"Sample": "Hello World"}

    req = requests.put(url, json=data, headers=headers)
    print(req.text)


def delete():
    url = 'https://api.jsonbin.io/b/<BIN_ID>'
    headers = {'secret-key': current_app.config.get('JSONBIN_API_KEY')}

    req = requests.delete(url, json=nil, headers=headers)
    print(req.text)