import requests, json
from flask import current_app


def create_subscriber(email):
    url = "https://api.mailerlite.com/api/v2/groups/27065448/subscribers"

    data = {
        'email': email,
    }

    payload = json.dumps(data)

    headers = {
        'content-type': "application/json",
        'x-mailerlite-apikey': current_app.config.get('MAILERLITE_API_KEY')
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    print(response.text)


def get_groups():
    url = "https://api.mailerlite.com/api/v2/groups"

    headers = {
        'content-type': "application/json",
        'x-mailerlite-apikey': current_app.config.get('MAILERLITE_API_KEY')
    }

    response = requests.request("GET", url, headers=headers)

    print(response.text)