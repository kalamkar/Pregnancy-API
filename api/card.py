'''
Created on Jul 28, 2015

@author: abhi
'''

import api
import datetime
import math
import re
import webapp2

from utils import weekly_cards
from utils import system_cards
from utils import data_cards
from datastore import Card
from api.renderer import get_card_json
from api.search import update_index
from api.event import get_average_measurement

from google.appengine.ext import ndb

class CardAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
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
        update_index(card)

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

        future = card.put_async()
        api.write_message(self.response, 'Successfully updated the card')
        update_index(future.get_result())

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
    cards.extend(get_data_cards(user))

    var_pattern = re.compile('%([a-z0-9-_]*)%')
    var_values = get_card_variables(user)
    var_keys = var_values.keys()
    futures = []
    # Add new cards
    for card in cards:
        missing_variable_value = False
        match = var_pattern.search(card.text)
        var_names = match.groups() if match else []
        for variable in var_names:
            if variable in var_keys:
                card.text = card.text.replace('%' + variable + '%', str(var_values[variable]))
            else:
                missing_variable_value = True

        if missing_variable_value:
            continue

        if card.text in current_cards.keys():
            continue

        futures.append(card.put_async())

    if get_due_date(user):
        for text, card in current_cards.iteritems():
            if 'action:due_date' in card.tags:
                card.key.delete_async()

    for future in futures:
        update_index(future.get_result())


def get_system_cards(user):
    priority = 3
    cards_by_tag = {}
    for content in system_cards.data['cards']:
        card = make_card(content, user)
        card.priority = priority
        priority += 1
        for tag in card.tags:
            if not tag in cards_by_tag.keys():
                cards_by_tag[tag] = []
            cards_by_tag[tag].append(card)

    cards = []
    for tag in get_user_tags(user):
        if tag in cards_by_tag.keys():
            cards.extend(cards_by_tag[tag])

    return cards

def get_data_cards(user):
    cards = []
    for content in data_cards.data['cards']:
        card = make_card(content, user)
        card.priority = 2
        cards.append(card)

    return cards

def get_week_based_cards(user):
    due_date = get_due_date(user)
    if not due_date:
        return []

    start_date = due_date - datetime.timedelta(weeks=40)
    week = int((datetime.datetime.now() - start_date).days / 7)

    try:
        contents = weekly_cards.weekly['weeks'][str(week)]['cards']
        if not contents:
            return []
    except:
        return []

    cards_by_tag = {}
    card_objects = []
    for content in contents:
        card = make_card(content, user)
        # Let the card expire in 1 week (counting weeks from start_date and not 1 week from now)
        card.expire_time = start_date + datetime.timedelta(weeks=week + 1)
        card_objects.append(card)

        # Add them to a dict by tag for priority
        for tag in card.tags:
            if not tag in cards_by_tag.keys():
                cards_by_tag[tag] = []
            cards_by_tag[tag].append(card)

    # Get the priority in this order: Size, Symptom1, Poll1, Care, Tips, Symptoms
    priority = 3
    if 'size' in cards_by_tag.keys():
        card = cards_by_tag['size'].pop(0)
        card.priority = 0
    if 'symptom' in cards_by_tag.keys():
        card = cards_by_tag['symptom'].pop(0)
        card.priority = priority
        priority += 1
    if 'poll' in cards_by_tag.keys():
        card = cards_by_tag['poll'].pop(0)
        card.priority = priority
        priority += 1
    if 'care' in cards_by_tag.keys():
        card = cards_by_tag['care'].pop(0)
        card.priority = priority
        priority += 1

    for card in card_objects:
        if card.priority >= 99:
            card.priority = priority
            priority += 1

    return card_objects

def get_due_date(user):
    for feature in user.features:
        if feature.name == 'DUE_DATE_MILLIS':
            return api.get_time_from_millis(feature.value)
    return None

def make_card(content, user):
    keys = content.keys()
    card = Card(parent=user.key)
    card.text = content['text'].decode('utf-8', 'ignore') if 'text' in keys else None
    card.icon = content['icon'] if 'icon' in keys else None
    card.image = content['image'] if 'image' in keys else None
    card.url = content['url'] if 'url' in keys else None
    card.options = content['options'] if 'options' in keys else []
    card.tags = content['tags'] if 'tags' in keys else []
    card.priority = int(content['priority']) if 'priority' in keys else 99
    if 'expire_seconds' in keys:
        seconds = int(content['expire_seconds'])
        card.expire_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    if 'expire_time' in keys:
        card.expire_time = api.get_time_from_millis(content['expire_time'])
    return card

def get_user_tags(user):
    tags = []
    if (datetime.datetime.now() - user.create_time).total_seconds() < 3600:
        tags.append('onboard')

    return tags

def get_card_variables(user):
    variables = {}
    variables['name'] = user.name if user.name else ''
    last_week_start = api.get_last_week_start()
    last_week_end = last_week_start + datetime.timedelta(days=7)
    weekly_avg_steps = get_average_measurement(user, 'STEPS', api.get_time_millis(last_week_start),
                                               api.get_time_millis(last_week_end))
    weekly_avg_sleep = get_average_measurement(user, 'SLEEP', api.get_time_millis(last_week_start),
                                               api.get_time_millis(last_week_end))
    if weekly_avg_steps and not math.isnan(weekly_avg_steps):
        variables['weekly_average_steps'] = str(int(weekly_avg_steps))
    if weekly_avg_sleep and not math.isnan(weekly_avg_sleep):
        variables['weekly_average_sleep'] = str(weekly_avg_sleep)
    return variables

