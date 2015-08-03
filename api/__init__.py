'''
Created on Mar 18, 2015

@author: abhijit
'''

import binascii
import config
import datetime
import json
import logging
import re
import sys
import StringIO
import socket
import ssl
import struct


from datastore import Location
from datastore import User
from google.appengine.api import mail
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
    try:
        auth_header = request.headers['Authorization']
    except KeyError:
        auth_header = request.get('auth')

    if auth_header:
        uuid, auth = get_uuid_auth(auth_header)
        if uuid and auth:
            user = User.query(User.uuid == uuid).get()
            if user and user.auth == auth:
                return user

    return None

def get_uuid_auth(auth_header):
    m = re.search('^(UUID-TOKEN) *(uuid)="(.*)" *, *(token)="(.*)"$', auth_header)
    if not m:
        logging.warn('Invalid authorization header %s' % (auth_header))
        return (None, None)
    try:
        if not m.group(1) == 'UUID-TOKEN':
            return (None, None)
        return(m.group(3), m.group(5))
    except IndexError:
        logging.warn('Invalid authorization header %s' % (auth_header))

    return (None, None)


def is_user_allowed_message_view(user, message):
    if message.sender == user.key:
        return True
    # TODO(abhi): allow messages to groups that user is member of
    return message.key.parent().get().public

def is_user_allowed_group_view(user, group):
    return group.public or user.key in group.members



def apns(token, message, gateway):
    if not token or not message:
        logging.warn('Invalid token or message')

    payload = json.dumps({"aps": {"alert" : message, "sound": "bingbong.aiff"}})

    if gateway == 'sandbox':
        sock = ssl.wrap_socket(socket.socket(),
                                server_side=False,
                                keyfile=StringIO.StringIO(config.KEY_DEV),
                                certfile=StringIO.StringIO(config.CERT_DEV))
        sock.connect(config.APNS_DEV)
    else:
        sock = ssl.wrap_socket(socket.socket(),
                                server_side=False,
                                keyfile=StringIO.StringIO(config.KEY),
                                certfile=StringIO.StringIO(config.CERT))
        sock.connect(config.APNS)


    logging.info('token is %s' % (token))
    token = binascii.unhexlify(token)
    fmt = "!cH32sH{0:d}s".format(len(payload))
    cmd = '\x00'
    msg = struct.pack(fmt, cmd, len(token), token, len(payload), payload)
    sock.write(msg)
    sock.close()

def gcm(tokens, data):
    payload = {'registration_ids': tokens, 'data': data}
    headers = {'Content-Type': 'application/json',
               'Authorization': 'key=' + config.GCM_API_KEY}
    logging.info(json.dumps(payload))
    result = urlfetch.fetch(url=config.GCM_URL,
                            payload=json.dumps(payload),
                            method=urlfetch.POST,
                            headers=headers)
    logging.info(result.content)

def email(address, message):
    if not mail.is_email_valid(address):
        logging.info('Invalid email address %s' % (address))
        return

    sender_address = "Dovetail.care Support <support@dovetail-api1.appspotmail.com>"
    mail.send_mail(sender_address, address, message, message)

