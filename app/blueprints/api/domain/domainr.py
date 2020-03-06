from flask import current_app
from app.blueprints.api.api_functions import print_traceback
import requests
import json


def get_domain_status(domain):
    try:
        api_key = current_app.config.get('X_RAPID_API_KEY')
        url = "https://domainr.p.rapidapi.com/v2/status"
        querystring = {"domain": domain}

        headers = {
            'x-rapidapi-host': "domainr.p.rapidapi.com",
            'x-rapidapi-key': api_key
        }

        r = requests.get(url=url, headers=headers, params=querystring)
        results = json.loads(r.text)['status']

        if len(results) > 0 and 'status' in results[0] and results[0]['status'] == 'deleting':
            return True
        return False
    except Exception as e:
        print_traceback(e)
    return None
