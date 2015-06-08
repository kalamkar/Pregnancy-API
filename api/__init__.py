'''
Created on Mar 18, 2015

@author: abhijit
'''

import binascii
import config
import datetime
import json
import logging
import sys
import StringIO
import socket
import ssl
import struct


from datastore import Location
from google.appengine.api import urlfetch
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



def apns(token, message, gateway):
    payload = json.dumps({"aps": {"alert" : message, "sound": "bingbong.aiff"}})

    if gateway == 'sandbox':
        sock = ssl.wrap_socket(socket.socket(),
                                server_side=False,
                                keyfile=StringIO.StringIO(config.KEY_DEV),
                                certfile=StringIO.StringIO(config.CERT_DEV),
                                ssl_version=ssl.PROTOCOL_SSLv3)
        sock.connect(config.APNS_DEV)
    else:
        sock = ssl.wrap_socket(socket.socket(),
                                server_side=False,
                                keyfile=StringIO.StringIO(config.KEY),
                                certfile=StringIO.StringIO(config.CERT),
                                ssl_version=ssl.PROTOCOL_SSLv3)
        sock.connect(config.APNS)


    token = binascii.unhexlify(token)
    fmt = "!cH32sH{0:d}s".format(len(payload))
    cmd = '\x00'
    msg = struct.pack(fmt, cmd, len(token), token, len(payload), payload)
    sock.write(msg)
    sock.close()

def gcm(tokens, message):
    payload = {'registration_ids': tokens, 'data': {'message': message}}
    headers = {'Content-Type': 'application/json',
               'Authorization': 'key=' + config.GCM_API_KEY}
    result = urlfetch.fetch(url=config.GCM_URL,
                            payload=json.dumps(payload),
                            method=urlfetch.POST,
                            headers=headers)
    logging.info(result.content)

def email(address, message):
    pass
