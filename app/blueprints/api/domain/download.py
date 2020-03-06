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
from collections import OrderedDict


def pool_domains(limit):
    try:
        from app.blueprints.api.api_functions import pool_tlds, valid_tlds
        results = list()

        # Download the list of PendingDelete domains
        url = 'https://www.pool.com/Downloads/PoolDeletingDomainsList.zip'
        request = requests.get(url)
        f = zipfile.ZipFile(BytesIO(request.content))
        for name in f.namelist():
            data = f.read(name).decode("utf-8")

            tlds = pool_tlds()
            tld_length = len(tlds)

            domain_list = list()

            # Split the lines from the downloaded file and filter out the TLDs we want
            lines = data.splitlines()
            lines = filter_tlds(lines, tlds)

            for tld in tlds:
                counter = 0

                for line in lines:
                    if tld in line:
                        domain_list.append(line)
                        counter += 1

                    # Add a max of (limit) domains per TLD to the list
                    if counter == limit or len(domain_list) == limit * tld_length:
                        break

            # Each line is comma separated, turn each into a list
            domains = [i.split(',') for i in domain_list]

            # Shuffle the results
            # random.shuffle(domains)

            # Choose X of them at random
            # domains = random.sample(domains, limit)

            # Add the domains to a dictionary
            for domain in domains:
                results.append({'name': domain[0], 'date_available': domain[1].replace(' 12:00:00 AM', '')})

                # Limit the number of results to max 100 per tld
                if len(results) == limit * tld_length:
                    break

        return results
    except Exception as e:
        print_traceback(e)
        return []


def park_domains(limit):
    try:
        from app.blueprints.page.date import convert_string_dates
        from app.blueprints.api.api_functions import park_tlds
        tlds = park_tlds()
        results = list()

        url = 'https://park.io/domains/index/all.json?limit=10000'
        r = requests.get(url=url)
        d = random.sample(json.loads(r.text)['domains'], k=int(limit * len(tlds)))

        # random.shuffle(d)

        for tld in tlds:
            domains = [x for x in d if x['name'].endswith(tld)]
            for domain in domains:
                results.append({'name': domain['name'], 'date_available': convert_string_dates(domain['date_available'])})

                # Limit the number of results
                if len(results) == limit * len(tlds):
                    break

        # random.shuffle(results)
        return results
    except Exception as e:
        print_traceback(e)
        return []


def filter_tlds(domains, tlds):
    # Return domains that end in our selected TLDs, and don't have a double hyphen in them.
    return [x for x in domains if any(tld in x for tld in tlds) and '--' not in x]
