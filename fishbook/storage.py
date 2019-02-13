from __future__ import absolute_import

import datetime
import secrets
from flask import current_app
from google.cloud import storage
import six
from werkzeug import secure_filename
from werkzeug.exceptions import BadRequest


def _get_storage_client():
    return storage.Client(
        project=current_app.config['PROJECT_ID'])


def _check_extension(filename, allowed_extensions):
    if ('.' not in filename or
            filename.split('.').pop().lower() not in allowed_extensions):
        raise BadRequest(
            "{0} has an invalid name or extension".format(filename))


def _safe_filename(filename):

    random_hex = secrets.token_hex(16)

    """
    filename = secure_filename(filename)
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    basename, extension = filename.rsplit('.', 1)
    return "{0}-{1}.{2}".format(basename, date, extension)
    """
    basename, extension = filename.rsplit('.', 1)
    return "{0}.{1}".format(random_hex, extension)

def get_blob(filename, type, bucket):
    if type == 1 :
        blob = bucket.blob('static/profile_pics/'+filename)
    elif type == 2 :
        blob = bucket.blob('static/post_pics/'+filename)
    elif type == 3 :
        blob = bucket.blob('static/fish_pics/'+filename)
    elif type == 4 :
        blob = bucket.blob('static/upload_pics/'+filename)
    return blob

# [START upload_file]
def upload_file(file_stream, filename, content_type, type):
    """
    Uploads a file to a given Cloud Storage bucket and returns the public url
    to the new object.
    """
    _check_extension(filename, current_app.config['ALLOWED_EXTENSIONS'])
    filename = _safe_filename(filename)

    client = _get_storage_client()
    bucket = client.bucket(current_app.config['CLOUD_STORAGE_BUCKET'])
    blob = get_blob(filename, type, bucket)
    blob.upload_from_string(
        file_stream,
        content_type=content_type)

    url = blob.public_url

    if isinstance(url, six.binary_type):
        url = url.decode('utf-8')

    return filename
# [END upload_file]
def delete_blob(filename, type):
    """Deletes a blob from the bucket."""
    _check_extension(filename, current_app.config['ALLOWED_EXTENSIONS'])
    client = _get_storage_client()
    bucket = client.bucket(current_app.config['CLOUD_STORAGE_BUCKET'])
    blob = get_blob(filename, type, bucket)
    blob.delete()

    return 'Blob {} deleted.'.format(filename)
