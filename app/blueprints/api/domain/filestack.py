from filestack import Filelink, Client
from flask import current_app
from app.blueprints.api.models.filestack import Filestack
from app.blueprints.api.api_functions import print_traceback
from app.extensions import db
from ast import literal_eval
from itertools import islice
import json
import random


def upload(file, count):
    client = Client(current_app.config.get('FILESTACK_API_KEY'))
    link = client.upload(filepath=file.name)
    if link.url:
        f = Filestack()
        f.name = file.name
        f.url = link.url
        f.handle = link.handle
        f.count = '{:,}'.format(count)
        f.save()


def get_content(limit=None, get_count=False):
    from app.blueprints.api.domain.domain import generate_drops
    f = db.session.query(Filestack).order_by(Filestack.id.desc()).first()

    if f is None:
        generate_drops()

    try:
        handle = f.handle
        filelink = Filelink(handle)
        domains = list()#

        if get_count:
            return f.count

        if limit is not None:
            for x in range(limit):
                line = random.choice((filelink.get_content().decode("utf-8")).splitlines())
                domains.append(json.loads(line))
            return domains
        else:
            data = filelink.get_content().decode("utf-8")
            for line in data.splitlines():
                domains.append(json.loads(line))
            return domains
    except Exception as e:
        print_traceback(e)
        generate_drops()
        return []