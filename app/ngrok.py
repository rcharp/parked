import json
import os
import requests
from urllib.request import urlopen


os.system("curl  http://localhost:4040/api/tunnels > tunnels.json")


def get_ngrok_url():
    url = "http://localhost:4040/api/tunnels/"
    response = urlopen(url)
    data = response.read()
    values = json.loads(data)
    print(values)
