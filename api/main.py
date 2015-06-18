#!/usr/bin/python2.7

""" APIs module
"""

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

import webapp2
from google.appengine.ext import ndb

from api.event import EventAPI
from api.group import GroupAPI
from api.message import MessageAPI
from api.search import SearchAPI
from api.user import UserAPI
from api.user import UserPhotoAPI
from api.appointment import AppointmentAPI

app = ndb.toplevel(webapp2.WSGIApplication([
    ('/event', EventAPI),
    ('/search', SearchAPI),
    ('/group', GroupAPI),
    ('/message', MessageAPI),
    ('/user', UserAPI),
    ('/user/photo', UserPhotoAPI),
    ('/appointment', AppointmentAPI)
], debug=False))