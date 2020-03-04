import urllib.request as urllib2
import requests
import zipfile
from io import BytesIO
import json


def dl_file():

    from app.blueprints.api.api_functions import dropping_tlds

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

