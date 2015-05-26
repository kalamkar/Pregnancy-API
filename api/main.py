#!/usr/bin/python2.7

""" APIs module
"""

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

import webapp2
from google.appengine.ext import ndb

from api.event import EventAPI
from api.group import GroupAPI
from api.message import MessageAPI
from api.user import UserAPI

app = ndb.toplevel(webapp2.WSGIApplication([
    ('/event', EventAPI),
    ('/group', GroupAPI),
    ('/message', MessageAPI),
    ('/user', UserAPI)
], debug=False))