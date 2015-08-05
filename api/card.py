'''
Created on Jul 28, 2015

@author: abhi
'''

import api
import datetime
import webapp2

from utils import weekly_cards
from utils import system_cards
from datastore import Card
from api.renderer import get_card_json

from google.appengine.ext import ndb

class CardAPI(webapp2.RequestHandler):

    def post(self):
        self.put()

    def put(self):
        card_id = self.request.get('card_id')
        tag = self.request.get('tag')
        tags = self.request.get('tags')

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
        elif tag:
            card.tags.append(tag.lower())

        card.put_async()
        api.write_message(self.response, 'Successfully updated the card')

    def get(self):
        tags = self.request.get('tags')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        cards = []
        if tags:
            query = Card.query(Card.tags.IN(tags.lower().split(',')),
                               ancestor=user.key).order(-Card.create_time)
        else:
            query = Card.query(ancestor=user.key).order(-Card.create_time)

        for card in query:
            cards.append(get_card_json(card))

        api.write_message(self.response, 'success', extra={'cards' : cards})


def update_user_cards(user):
    current_cards = {}
    for card in Card.query(ancestor=user.key):
        current_cards[card.text] = card

    cards = get_system_cards(user)
    cards.extend(get_week_based_cards(user))

    # Add new cards
    for card in cards:
        card.text = card.text.replace('%name%', user.name.split()[0] if user.name else '')

        if card.text in current_cards.keys():
            continue

        card.put_async()

    if get_due_date(user):
        for text, card in current_cards.iteritems():
            if 'action:due_date' in card.tags:
                card.key.delete_async()


def get_system_cards(user):
    tagged_cards = {}
    for content in system_cards.data['cards']:
        card = make_card(content, user)
        for tag in card.tags:
            if not tag in tagged_cards.keys():
                tagged_cards[tag] = []
            tagged_cards[tag].append(card)

    cards = []
    for tag in get_user_tags(user):
        if tag in tagged_cards.keys():
            cards.extend(tagged_cards[tag])

    return cards

def get_week_based_cards(user):
    due_date = get_due_date(user)
    if not due_date:
        return []

    start_date = due_date - datetime.timedelta(weeks=40)
    week = int((datetime.datetime.now() - start_date).days / 7)

    contents = weekly_cards.weekly['weeks'][str(week)]['cards']
    if not contents:
        return []
    priority = 1
    card_objects = []
    for content in contents:
        card = make_card(content, user)
        card.priority = 0 if 'size' in card.tags else priority
        priority += 1
        # Let the card expire in 1 week (counting weeks from start_date and not 1 week from now)
        card.expire_time = start_date + datetime.timedelta(weeks=week + 1)
        card_objects.append(card)
    return card_objects

def get_due_date(user):
    for feature in user.features:
        if feature.name == 'DUE_DATE_MILLIS':
            return datetime.datetime.utcfromtimestamp(int(feature.value) // 1000)
    return None

def make_card(content, user):
    keys = content.keys()
    card = Card(parent=user.key)
    card.text = content['text'] if 'text' in keys else None
    card.icon = content['icon'] if 'icon' in keys else None
    card.image = content['image'] if 'image' in keys else None
    card.url = content['url'] if 'url' in keys else None
    card.options = content['options'] if 'options' in keys else []
    card.tags = content['tags'] if 'tags' in keys else []
    return card

def get_user_tags(user):
    tags = []
    if (datetime.datetime.now() - user.create_time).total_seconds() < 3600:
        tags.append('onboard')

    return tags
