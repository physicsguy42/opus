from results.views import *
from tools.views import *
from user_collections.views import *
from django.contrib.sessions.models import Session
from django.core import serializers
from django.http import HttpResponse
from django.db.models import Sum
import settings
import StringIO
import tarfile
import random
import string
import datetime
import hashlib
import os

import logging
log = logging.getLogger(__name__)

def create_zip_filename(ring_obs_id=None):
    if not ring_obs_id:
        letters = random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters)
        timestamp = "T".join(str(datetime.datetime.now()).split(' '))
        return 'pdsdata_' + letters + '_' + timestamp + '.tgz'
    else:
        return "pdsdata_uni_" + ring_obs_id + '.tgz'

def md5(filename):
    ''' function to get md5 of file '''
    d = hashlib.md5()
    try:
        d.update(open(filename).read())
    except Exception,e:
        pass
        # print e
    else:
        return d.hexdigest()


def get_download_size(files, product_types, previews):
    # takes file_names as returned by getFiles()
    # returns size in bytes as int
    urls = []
    for ring_obs_id in files:
        for ptype in files[ring_obs_id]:
            if (not product_types) | (ptype in product_types.split(',')):
                urls += [files[ring_obs_id][ptype] for ptype in files[ring_obs_id]][0] # list of all urls

    file_names = [('/').join(u.split('/')[4:len(u)]) for u in urls] # split off domain and directory, that's how their stored in file_sizes
    try:
        size = FileSizes.objects.filter(name__in=file_names).aggregate(Sum('size'))['size__sum']
    except TypeError:
        size = 0    # no file found, move along

    return size  # bytes!

# http://pds-rings.seti.org/volumes/
def get_download_info(request, collection=""):
    if not collection:
        from user_collections.views import * # circumvent the circular dependency.. James Bennett say so!
        collection = get_collection(request)

    fmt = request.GET.get('fmt', None)
    product_types = request.GET.get('types', '')
    previews = request.GET.get('previews', '')

    # make a flat list of file_names
    urls = []
    from results.views import *
    files = getFiles(collection, "raw", "url", product_types, previews)

    for ring_obs_id in files:
        for ptype in files[ring_obs_id]:
            if (not product_types) | (ptype in product_types.split(',')):
                urls += [files[ring_obs_id][ptype] for ptype in files[ring_obs_id]][0] # list of all urls

    count = len(urls)

    size = get_download_size(files, product_types, previews)

    if size > 1000:
        size = str(size/1024) + " GB"
    else:
        size = str(size) + " MB"

    if fmt == 'json':
        return HttpResponse(simplejson.dumps({'size':size, 'count':count}), mimetype='application/json')
    else:
        return {'size':size, 'count':count}



def get_cum_downlaod_size(request, download_size):
    cum_downlaod_size = int(download_size) if download_size else 0
    if request.session.get('cum_downlaod_size'):
        cum_downlaod_size = request.session.get('cum_downlaod_size') + int(download_size)
    request.session['cum_downlaod_size'] = cum_downlaod_size
    return cum_downlaod_size

def create_download(request, collection_name='', ring_obs_ids=None, fmt="raw"):

    fmt = request.GET.get('fmt', None)
    product_types = request.GET.get('types', '')
    previews = request.GET.get('previews', '')

    if not ring_obs_ids:
        ring_obs_ids = []
        from user_collections.views import *
        ring_obs_ids = get_collection(request, collection_name);

    # get product info about this product
    # [optimize] [cleanup] this should use from db rather than string of text https://docs.djangoproject.com/en/1.3/ref/models/querysets/

    if type(ring_obs_ids) is unicode:
        # a single ring_obs_id
        zip_file_name = create_zip_filename(ring_obs_ids);
        ring_obs_ids = [ring_obs_ids]
    else:
        zip_file_name = create_zip_filename();

    chksum_file_name = settings.TAR_FILE_PATH + "checksum_" + zip_file_name.split(".")[0] + ".txt"
    manifest_file_name = settings.TAR_FILE_PATH + "manifest_" + zip_file_name.split(".")[0] + ".txt"

    # lisa
    from results.views import *
    files = getFiles(ring_obs_ids,"raw", "path", product_types, previews)
    # return getFiles(ring_obs_ids,"raw", loc_type = 'path')
    #
    # files = getFiles(ring_obs_ids,"raw", "url", product_types, previews)
    # return HttpResponse(simplejson.dumps(files), mimetype="application/json")

    tar = tarfile.open(settings.TAR_FILE_PATH + zip_file_name, 'w:gz')
    chksum = open(chksum_file_name,"w")
    manifest = open(manifest_file_name,"w")
    size = get_download_size(files, product_types, previews)

    """
    cum_downlaod_size = get_cum_downlaod_size(request,size)
    if cum_downlaod_size > settings.MAX_CUM_DOWNLAOD_SIZE:
        # user is trying to download > MAX_CUM_DOWNLAOD_SIZE
        return HttpResponse("Sorry, Max cumulative download size reached " + str(cum_downlaod_size) + ' > ' + str(settings.MAX_CUM_DOWNLAOD_SIZE))
    """

    errors = []
    added = False
    for ring_obs_id,products in files.items():
        for product_type,file_list in products.items():
            for name in file_list:
                try:
                    digest="%s:%s"%(name.split("/")[-1], md5(name))
                    mdigest="%s:%s"%(ring_obs_id, name.split("/")[-1])
                    chksum.write(digest+"\n")
                    manifest.write(mdigest+"\n")
                    tar.add(name, arcname=name.split("/")[-1]) # arcname = fielname only, not full path
                    added = True
                except Exception,e:
                    errors.append("could not find: " + name.split("/")[-1])
                    # print "could not find " + name


    manifest.write("errors:"+"\n")
    for e in errors:
        manifest.write(e+"\n")

    manifest.close()
    chksum.close()
    tar.add(chksum_file_name, arcname="checksum.txt")
    tar.add(manifest_file_name, arcname="manifest.txt")
    tar.close()

    zip_url = settings.TAR_FILE_URI_PATH + zip_file_name

    if not added:
        zip_url = "No Files Found"

    if fmt == 'json':
        return HttpResponse(simplejson.dumps(zip_url), mimetype='application/json')

    return HttpResponse(zip_url)

