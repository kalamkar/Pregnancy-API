'''
Created on Jul 28, 2015

@author: abhi
'''

import api
import config
import webapp2

from datastore import Card
from datastore import User
from api.renderer import get_card_json
from utils.user_card_creator import make_card

from google.appengine.ext import ndb

class CardAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
            self.put()
            return
        if self.request.get('_delete'):
            self.put()
            return

        text = self.request.get('text')
        tags = self.request.get('tags')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if not tags or not text:
            api.write_error(self.response, 400, 'Missing required parameter')
            return

        content = {'tags': tags.lower().split(','),
                   'text': text,
                   'priority': self.request.get('priority'),
                   'image': self.request.get('image'),
                   'icon': self.request.get('icon'),
                   'url': self.request.get('url'),
                   'expire_time': self.request.get('expire_time'),
                   'options': self.request.get_all('option') }
        card = make_card(content, user)
        card.put()

        api.write_message(self.response, 'Successfully added card %s' % (card.key.urlsafe()))
        api.search.update_private_index(card, user.uuid)

    def put(self):
        card_id = self.request.get('card_id')
        tag = self.request.get('tag')
        tags = self.request.get('tags')
        text = self.request.get('text')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return
        if not card_id:
            api.write_error(self.response, 400, 'Missing required parameter')
            return
        if not tag and not tags:
            api.write_error(self.response, 400, 'Missing parameter to update')
            return

        card = ndb.Key(urlsafe=card_id).get()
        if not card:
            api.write_error(self.response, 404, 'Card not found')
            return

        if tags:
            card.tags = tags.lower().split(',')
        elif tag and not tag.lower() in card.tags:
            card.tags.append(tag.lower())

        card.text = text if text else card.text

        card.put()
        api.write_message(self.response, 'Successfully updated the card')
        api.search.update_private_index(card, user.uuid)

    def get(self):
        tags = self.request.get('tags')
        public = self.request.get('public')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if public:
            user = User.query(User.uuid == config.SUPER_USER_UUID).get()

        cards = []
        if tags:
            tags = tags.lower().split(',')
            query = Card.query(Card.tags.IN(tags), ancestor=user.key).order(-Card.create_time)
        else:
            query = Card.query(ancestor=user.key).order(-Card.create_time)

        for card in query:
            cards.append(get_card_json(card))

        api.write_message(self.response, 'success', extra={'cards' : cards})


    def delete(self):
        card_id = self.request.get('card_id')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        card = ndb.Key(urlsafe=card_id).get()
        if not card:
            api.write_error(self.response, 404, 'Card not found')
            return

        if not card.key.parent() == user.key:
            api.write_error(self.response, 403, 'Only owner of the card can delete it.')
            return

        api.search.delete_from_indices(card, user.uuid)
        card.delete_async()
        api.write_message(self.response, 'success')
