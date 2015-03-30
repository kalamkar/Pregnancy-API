#!/usr/bin/python2.7

""" Datastore classes
"""

__author__ = 'abhi@teddytab.com (Abhijit Kalamkar)'

from google.appengine.ext import ndb

class Device(ndb.Model):
    uuid = ndb.StringProperty(required=True)
    device_type = ndb.StringProperty(choices=['UNKNOWN', 'GOOGLE', 'APPLE', 'AMAZON'])
    push_token = ndb.StringProperty()
    model = ndb.StringProperty()
    update_time = ndb.DateTimeProperty(auto_now=True)
    create_time = ndb.DateTimeProperty(auto_now_add=True)

class Event(ndb.Model):
    event_type = ndb.StringProperty()
    time = ndb.DateTimeProperty()
    create_time = ndb.DateTimeProperty(auto_now_add=True)


