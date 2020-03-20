import io
import json
import boto3
import random
from os import path
from flask import current_app
from botocore.exceptions import NoCredentialsError
from app.blueprints.api.api_functions import print_traceback


def upload_to_aws(local_file, bucket, s3_file):
    ACCESS_KEY = current_app.config.get('AWS_ACCESS_KEY_ID')
    SECRET_KEY = current_app.config.get('AWS_ACCESS_KEY_SECRET')

    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        # print("Upload Successful")
        return True
    except FileNotFoundError:
        # print("The file was not found")
        return False
    except NoCredentialsError:
        # print("Credentials not available")
        return False
    except Exception as e:
        print_traceback(e)
        return False


def download_from_aws(filename):
    ACCESS_KEY = current_app.config.get('AWS_ACCESS_KEY_ID')
    SECRET_KEY = current_app.config.get('AWS_ACCESS_KEY_SECRET')

    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.download_file('namecatcherio', filename, filename)
        return True
    except Exception as e:
        print_traceback(e)
        return False


def get_last_modified():
    ACCESS_KEY = current_app.config.get('AWS_ACCESS_KEY_ID')
    SECRET_KEY = current_app.config.get('AWS_ACCESS_KEY_SECRET')

    s3 = boto3.resource('s3', aws_access_key_id=ACCESS_KEY,
                        aws_secret_access_key=SECRET_KEY)

    bucket = s3.Bucket('namecatcherio')

    for file in bucket.objects.all():
        if file.key == 'domains.json':
            return file.last_modified


def get_content(limit=None, get_count=False):
    from app.blueprints.api.domain.domain import generate_drops

    if not path.exists("domains.json"):
        success = download_from_aws('domains.json')
        if not success:
            generate_drops()

    if get_count:
        return sum(1 for line in open('domains.json'))

    with open('domains.json', 'r') as output:
        try:
            domains = list()
            lines = output.read().splitlines()
            if limit is not None:
                counter = 0
                words = open('app/blueprints/api/domain/words/words.txt').read().splitlines()

                selection = [x for x in lines if json.loads(x)['date_available'] != today]
                selection = random.sample(selection, k=int(len(selection) / 2))
                for line in selection:
                    line = json.loads(line)

                    if has_word(words, line):
                        domains.append(line)
                        counter += 1

                    if counter == limit: break

                # Shuffle the limited selection
                random.shuffle(domains)
                return domains
            else:
                for line in lines:
                    domains.append(json.loads(line))
                return domains
        except Exception as e:
            print_traceback(e)
            generate_drops()
            return []