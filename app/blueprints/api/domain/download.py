import urllib.request as urllib2
import requests
import zipfile
from io import BytesIO
import json
import os
import re
import random
from app.blueprints.api.models.drops import Drop
from app.blueprints.api.api_functions import print_traceback
from app.blueprints.api.domain.jsonbin import create
from app.extensions import db
from sqlalchemy import exists
from itertools import groupby
from collections import OrderedDict


def pool_domains(limit):
    try:
        from app.blueprints.api.api_functions import pool_tlds, valid_tlds

        # Download the list of PendingDelete domains
        url = 'https://www.pool.com/Downloads/PoolDeletingDomainsList.zip'
        request = requests.get(url)
        f = zipfile.ZipFile(BytesIO(request.content))
        for name in f.namelist():
            data = f.read(name).decode("utf-8")

            tlds = pool_tlds()

            # domain_list = list()

            # Split the lines from the downloaded file and filter out the TLDs we want
            lines = data.splitlines()
            lines = filter_tlds(lines, tlds)

            with open('domains.json', 'a') as output:
                for tld in tlds:
                    counter = 0

                    for line in lines:
                        if tld in line:
                            d = line.split(',')
                            # Ignore domains with double hyphens
                            if '--' in d[0]:
                                continue
                            # domain_list.append({'name': d[0], 'date_available': d[1].replace(' 12:00:00 AM', '')})
                            json.dump({'name': d[0], 'date_available': d[1].replace(' 12:00:00 AM', '')}, output)
                            output.write(os.linesep)

                            counter += 1

                        # Add a max of (limit) domains per TLD to the list
                        if counter == limit:
                            break
            return True
    except Exception as e:
        print_traceback(e)
        return False


def park_domains(limit):
    try:
        from app.blueprints.page.date import convert_string_dates
        from app.blueprints.api.api_functions import park_tlds
        tlds = park_tlds()

        url = 'https://park.io/domains/index/all.json?limit=10000'
        r = requests.get(url=url)
        d = random.sample(json.loads(r.text)['domains'], k=int(limit * len(tlds)))

        # random.shuffle(d)

        for tld in tlds:
            domains = [x for x in d if x['name'].endswith(tld)]

            with open('domains.json', 'a') as output:
                counter = 0
                for domain in domains:
                    json.dump({'name': domain['name'], 'date_available': convert_string_dates(domain['date_available'])}, output)
                    output.write(os.linesep)
                    counter += 1

                    # Limit the number of results
                    if counter == limit:
                        break

        return True
    except Exception as e:
        print_traceback(e)
        return False


def filter_tlds(domains, tlds):
    # Return domains that end in our selected TLDs, and don't have a double hyphen in them. Also don't want domains with more than 2 hyphens
    return [x for x in domains if any(tld in x for tld in tlds) and '--' not in x and x.count('-') <= 2]
