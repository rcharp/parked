import urllib.request as urllib2
import requests
import zipfile
from io import BytesIO
import json
import random
from app.blueprints.api.models.drops import Drop
from app.blueprints.api.api_functions import print_traceback
from app.extensions import db
from sqlalchemy import exists


def pool_domains():
    try:
        from app.blueprints.api.api_functions import dropping_tlds
        # count = 0
        results = list()

        url = 'https://www.pool.com/Downloads/PoolDeletingDomainsList.zip'
        request = requests.get(url)
        file = zipfile.ZipFile(BytesIO(request.content))
        for name in file.namelist():
            data = file.read(name).decode("utf-8")
            for sub in dropping_tlds():
                domains = [i.split(',') for i in data.splitlines(5) if sub in i]
                for domain in domains:
                    results.append({'name': domain[0], 'date_available': domain[1]})

                    if len(results) == 40:
                        break

        return results
    except Exception as e:
        print_traceback(e)
        return None


def park_domains():
    try:
        tlds = dropping_tlds()
        domains = list()

        for tld in tlds:
            url = 'https://park.io/domains/index/' + tld.replace('.', '') + '.json?limit=1000'
            r = requests.get(url=url)
            results = random.sample(json.loads(r.text)['domains'], k=20)

            random.shuffle(results)
            for result in results:
                domains.append({'name': result['name'], 'date_available': result['date_available']})

        random.shuffle(domains)
        return domains
    except Exception as e:
        print_traceback(e)
        return None


