'''
Created on Mar 18, 2015

@author: abhijit
'''

import datetime
import json
import logging
import sys

from datastore import Location
from google.appengine.ext import ndb

def write_error(response, code, message):
    response.headers['Content-Type'] = 'application/json'
    response.status_int = code
    response.out.write(json.dumps({'code': 'ERROR', 'message': message}))
    logging.warn("Error %d: %s" % (code, message))

def write_message(response, message, extra={}):
    response.headers['Content-Type'] = 'application/json'
    output = dict({'code': 'OK', 'message': message}.items() + extra.items())
    response.out.write(json.dumps(output))

def get_time_millis(time):
    # TODO(abhi): We are losing millisecond accuracy here, fix it.
    return int((time - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

def get_geo_point(request):
    try:
        latlon = request.headers['X-AppEngine-CityLatLong'].split(',')
        return Location(name=get_geo_name(request), latlon=ndb.GeoPt(latlon[0], latlon[1]))
    except:
        logging.warn(sys.exc_info()[0])

    logging.warn('Found no or invalid location headers')
    return None


def get_geo_name(request):
    name = request.headers.get('X-AppEngine-City')
    if name:
        return name.title()

    return get_region(request)


def get_region(request):
    region = request.headers.get('X-AppEngine-Region')
    if region:
        name = '%s-%s' % (request.headers.get('X-AppEngine-Country'), region.title())
    else:
        name = request.headers.get('X-AppEngine-Country')

    return name

def get_user(request):
    user_id = request.get('user_id')
    if not user_id:
        return None
    return ndb.Key(urlsafe=user_id).get()

def is_user_allowed_message_view(user, message):
    if message.sender == user.key:
        return True
    # TODO(abhi): allow messages to groups that user is member of
    return message.key.parent().get().public

def is_user_allowed_group_view(user, group):
    return group.public or user.key in group.members

