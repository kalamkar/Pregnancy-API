#!/usr/bin/python2.7

""" APIs module
"""

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

import webapp2
from google.appengine.ext import ndb

from api.event import EventAPI
from api.device import DeviceAPI

app = ndb.toplevel(webapp2.WSGIApplication([
    ('/device', DeviceAPI),
    ('/event', EventAPI)
], debug=False))