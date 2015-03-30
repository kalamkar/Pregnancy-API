#!/usr/bin/python2.7

""" Web module
"""

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

import webapp2
from google.appengine.ext import ndb

from web.chart import EventChart

app = ndb.toplevel(webapp2.WSGIApplication([
    ('/chart/events', EventChart)
], debug=False))