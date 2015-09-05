'''
Created on Aug 31, 2015

@author: abhi
'''

import jinja2
import logging
import os
import re
import sys
import web
import webapp2

from datastore import Card

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Poll(webapp2.RequestHandler):

    def get(self):
        data = {}
        try:
            poll_id = self.request.path.split('/')[2]
            card = Card.query(Card.tags == poll_id).get()
            data = {'options': card.options}
        except:
            web.write_error(self.response, 404, 'Card not found')
            return

        try:
            data['title'] = re.search('([^?\.!]+[?\.!]+)', card.text).group(0)
            data['text'] = card.text.replace(data['title'], '').strip()
        except:
            data['title'] = card.text
            logging.warn('Error splitting the title %s' % (sys.exc_info()[0]))

        data['tags'] = 'vote,' + ','.join(card.tags)
        data['result_image'] = '/event/chart?tags=' + poll_id
        template = JINJA_ENVIRONMENT.get_template('poll.html')
        self.response.write(template.render({'card': data, 'domain': self.request.host}))
