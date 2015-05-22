#!/usr/bin/python2.7

""" Datastore classes
"""
from lib2to3.pgen2.tokenize import group
from itertools import repeat

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

from google.appengine.ext import ndb

class Pair(ndb.Model):
    name = ndb.StringProperty()
    value = ndb.GenericProperty()

class Location(ndb.Model):
    latlon = ndb.GeoPtProperty()
    name = ndb.StringProperty()

class Event(ndb.Model):
    event_type = ndb.StringProperty()
    time = ndb.DateTimeProperty()
    create_time = ndb.DateTimeProperty(auto_now_add=True)

class Insight(ndb.Model):
    title = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    priority = ndb.IntegerProperty()
    
class Device(ndb.Model):
    device_type = ndb.StringProperty(required=True,  choices=['UNKNOWN', 'EMAIL', 'PHONE', \
                                                              'GOOGLE', 'APPLE', 'AMAZON'])
    data = ndb.StringProperty() # Push token, email address, phone number etc.
    auth = ndb.StringProperty()
    
class User(ndb.Model):    
    public_uuid = ndb.StringProperty()
    name = ndb.StringProperty()
    last_location = ndb.StructuredProperty(Location)
    devices = ndb.StructuredProperty(Device, repeated=True)
    features = ndb.StructuredProperty(Pair, repeated=True)
    insights = ndb.StructuredProperty(Insight, repeated=True)
    update_time = ndb.DateTimeProperty(auto_now=True)
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    
class Group(ndb.Model):
    name = ndb.StringProperty()
    uuid = ndb.StringProperty() # public
    users = ndb.StructuredProperty(User, repeated=True)
    

class Message(ndb.Model):
    sender = ndb.StructuredProperty(User)
    group = ndb.StructuredProperty(Group)
    text = ndb.TextProperty()
    media = ndb.StructuredProperty(Pair, repeated=True)

