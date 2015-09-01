'''
Created on Aug 31, 2015

@author: abhi
'''

import jinja2
import os
import re
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

        tokens = re.split('[?\.!]', card.text, maxsplit=1)
        if tokens and len(tokens) == 2:
            data['title'] = tokens[0]
            data['text'] = tokens[1]
        elif tokens and len(tokens) == 1:
            data['title'] = tokens[0]

        data['tags'] = 'vote,' + ','.join(card.tags)
        data['result_image'] = '/event/chart?tags=' + poll_id
        template = JINJA_ENVIRONMENT.get_template('poll.html')
        self.response.write(template.render({'card': data}))
