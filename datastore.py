#!/usr/bin/python2.7

""" Datastore classes
"""

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

from google.appengine.ext import ndb

# Generic structure for name value pair
class Pair(ndb.Model):
    name = ndb.StringProperty()
    value = ndb.GenericProperty()

# Part of User
class Location(ndb.Model):
    latlon = ndb.GeoPtProperty()
    name = ndb.StringProperty()

# Part of user
class Device(ndb.Model):
    device_type = ndb.StringProperty(required=True, choices=['UNKNOWN', 'EMAIL', 'PHONE', \
                                                             'GOOGLE', 'APPLE', 'AMAZON'])
    data = ndb.StringProperty()  # Push token, email address, phone number etc.


class Recovery(ndb.Model):
    code = ndb.IntegerProperty()
    time = ndb.DateTimeProperty(auto_now=True)

# Top level object representing a user
class User(ndb.Model):
    uuid = ndb.StringProperty()  # public
    auth = ndb.StringProperty()  # Password or token user to authenticate the user
    name = ndb.StringProperty()
    last_location = ndb.StructuredProperty(Location)
    devices = ndb.StructuredProperty(Device, repeated=True)
    features = ndb.StructuredProperty(Pair, repeated=True)
    recovery = ndb.StructuredProperty(Recovery)
    update_time = ndb.DateTimeProperty(auto_now=True)
    create_time = ndb.DateTimeProperty(auto_now_add=True)


# Child of User object representing a UI card
class Card(ndb.Model):
    text = ndb.StringProperty()
    icon = ndb.StringProperty()
    image = ndb.StringProperty()
    url = ndb.StringProperty()
    options = ndb.StringProperty(repeated=True)
    tags = ndb.StringProperty(repeated=True)
    priority = ndb.IntegerProperty()
    expire_time = ndb.DateTimeProperty()
    create_time = ndb.DateTimeProperty(auto_now_add=True)


# Child of User object representing an appointment or available slot
class Appointment(ndb.Model):
    consumer = ndb.KeyProperty(kind=User)  # optional, when null it is an available slot
    time = ndb.DateTimeProperty()
    minutes = ndb.IntegerProperty(default=60)
    update_time = ndb.DateTimeProperty(auto_now=True)
    create_time = ndb.DateTimeProperty(auto_now_add=True)


# Child of User object represents an event and optional data item
class Event(ndb.Model):
    event_type = ndb.StringProperty()
    time = ndb.DateTimeProperty()
    data = ndb.TextProperty()
    create_time = ndb.DateTimeProperty(auto_now_add=True)


# Top level object representing a chat among few users or even just two users
class Group(ndb.Model):
    name = ndb.StringProperty()  # Optional
    uuid = ndb.StringProperty()  # public visible
    public = ndb.BooleanProperty(default=False)
    admins = ndb.KeyProperty(kind=User, repeated=True)
    members = ndb.KeyProperty(kind=User, repeated=True)
    update_time = ndb.DateTimeProperty(auto_now=True)
    create_time = ndb.DateTimeProperty(auto_now_add=True)


# Lives within a Group
class Message(ndb.Model):
    sender = ndb.KeyProperty(kind=User)
    text = ndb.TextProperty()
    media = ndb.StructuredProperty(Pair, repeated=True)  # pair of content type and link to data
    create_time = ndb.DateTimeProperty(auto_now_add=True)


