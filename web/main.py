#!/usr/bin/python2.7

""" Web module
"""

__author__ = 'abhi@dovetail.care (Abhijit Kalamkar)'

import webapp2
from google.appengine.ext import ndb

from web.chart import EventChart
from web.poll import Poll

app = ndb.toplevel(webapp2.WSGIApplication([
    ('/chart/events', EventChart),
    ('/poll/.*', Poll)
], debug=False))