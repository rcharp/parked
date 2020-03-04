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
        from app.blueprints.api.api_functions import dropping_tlds, valid_tlds
        results = list()

        # Download the list of PendingDelete domains
        url = 'https://www.pool.com/Downloads/PoolDeletingDomainsList.zip'
        request = requests.get(url)
        f = zipfile.ZipFile(BytesIO(request.content))
        for name in f.namelist():
            data = f.read(name).decode("utf-8")

            tlds = dropping_tlds()
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
                    # lines.remove(line)

                    # Add a max of (limit) domains per TLD to the list
                    if counter == limit or len(domain_list) == limit * tld_length:
                        break

            # Each line is comma separated, turn each into a list
            domains = [i.split(',') for i in domain_list]
            # domains = filter_tlds(domains, dropping_tlds())

            # Shuffle the results
            # random.shuffle(domains)

            # Choose X of them at random
            # domains = random.sample(domains, limit)

            # Add the domains to a dictionary
            for domain in domains:
                results.append({'name': domain[0], 'date_available': domain[1]})

                # Limit the number of results to max 100 per tld
                if len(results) == limit * tld_length:
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
            domains = random.sample(json.loads(r.text)['domains'], k=int(limit))

            random.shuffle(domains)
            for domain in domains:
                results.append({'name': domain['name'], 'date_available': domain['date_available']})

                # Limit the number of results
                if len(results) == limit * len(tlds):
                    break

        random.shuffle(results)
        return results
    except Exception as e:
        print_traceback(e)
        return None


def filter_tlds(domains, tlds):
    # d = list()
    # for tld in tlds:
    #     for i in range(int(limit/len(tlds))):
    #         d.append([x for x in domains if any(tld in y[0] for y in x)])
    #
    #         if i == int(limit/len(tlds)):
    #             break
    #
    # return d
    return [x for x in domains if any(tld in x for tld in tlds)]
