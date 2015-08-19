#!/usr/bin/python2.7

""" APIs module
"""

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

import webapp2
from google.appengine.ext import ndb

from api.event import EventAPI
from api.event import EventChartAPI
from api.group import GroupAPI
from api.group import GroupPhotoAPI
from api.message import MessageAPI
from api.search import SearchAPI
from api.user import UserAPI
from api.user import UserPhotoAPI
from api.user import UserRecoveryAPI
from api.card import CardAPI
from api.appointment import AppointmentAPI

app = ndb.toplevel(webapp2.WSGIApplication([
    ('/event', EventAPI),
    ('/event/chart', EventChartAPI),
    ('/search', SearchAPI),
    ('/group', GroupAPI),
    ('/group/photo', GroupPhotoAPI),
    ('/message', MessageAPI),
    ('/user', UserAPI),
    ('/user/photo', UserPhotoAPI),
    ('/user/recover', UserRecoveryAPI),
    ('/user/card', CardAPI),
    ('/appointment', AppointmentAPI)
], debug=False))