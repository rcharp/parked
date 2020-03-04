import urllib.request as urllib2
import requests
import zipfile
from io import BytesIO
import json
import re
import random
from app.blueprints.api.models.drops import Drop
from app.blueprints.api.api_functions import print_traceback
from app.extensions import db
from sqlalchemy import exists
from itertools import groupby


def pool_domains(limit):
    try:
        from app.blueprints.api.api_functions import dropping_tlds, valid_tlds
        results = list()

        url = 'https://www.pool.com/Downloads/PoolDeletingDomainsList.zip'
        request = requests.get(url)
        file = zipfile.ZipFile(BytesIO(request.content))
        for name in file.namelist():
            data = file.read(name).decode("utf-8")

            # Split the lines from the csv and filter out the TLDs we want
            domains = [i.split(',') for i in data.splitlines()]
            domains = filter_tlds(domains, dropping_tlds(), limit)

            # Shuffle the results
            # random.shuffle(domains)

            # Choose X of them at random
            domains = random.sample(domains, limit)

            # Add the domains to a dictionary
            for domain in domains:
                results.append({'name': domain[0], 'date_available': domain[1]})

                # Limit the number of results
                if len(results) == limit:
                    break

        return results
    except Exception as e:
        print_traceback(e)
        return None


def park_domains(limit):
    try:
        from app.blueprints.api.api_functions import dropping_tlds
        tlds = dropping_tlds()
        results = list()

        for tld in tlds:
            url = 'https://park.io/domains/index/' + tld.replace('.', '') + '.json?limit=' + str(limit)
            r = requests.get(url=url)
            domains = random.sample(json.loads(r.text)['domains'], k=int(limit/len(tlds)))

            random.shuffle(domains)
            for domain in domains:
                results.append({'name': domain['name'], 'date_available': domain['date_available']})

                # Limit the number of results
                if len(results) == limit:
                    break

        random.shuffle(results)
        return results
    except Exception as e:
        print_traceback(e)
        return None


def filter_tlds(domains, tlds, limit):
    d = list()
    for tld in tlds:
        for i in range(int(limit/len(tlds))):
            d += [x for x in domains if any(tld in x[0])]

            if i == int(limit/len(tlds)):
                break

    return d
    # return [x for x in domains if any(tld in x[0] for tld in tlds)]
