'''
Created on Jul 28, 2015

@author: abhi
'''

import datetime
import logging

from utils import cards
from datastore import Card


def update_user_cards(user):
    current_cards = {}
    for card in Card.query(ancestor=user.key):
        current_cards[card.text + ','.join(card.tags)] = card

    due_date = get_due_date(user)
    if not due_date:
        logging.warn('Due date not available for user.')
        return
    start_date = due_date - datetime.timedelta(weeks=40)
    week = int((datetime.datetime.now() - start_date).days / 7)

    # Delete old cards
    for key, card in current_cards.iteritems():
        if card.expire_time < datetime.datetime.now():
            card.delete_async()
            current_cards.pop(key)

    # Add new cards
    for card in get_week_based_cards(week, user):
        key = card.text + ','.join(card.tags)
        if key in current_cards.keys():
            continue

        # Let the card expire in 1 week (counting weeks from start_date and not 1 week from now)
        card.expire_time = start_date + datetime.timedelta(weeks=week + 1)
        card.parent = user.key
        card.put_async()


def get_week_based_cards(week, user):
    contents = cards.data['weeks'][str(week)]['cards']
    if not contents:
        return []
    priority = 1
    card_objects = []
    for content in contents:
        keys = content.keys()
        card = Card(parent=user.key)
        card.text = content['text'] if 'text' in keys else None
        card.icon = content['icon'] if 'icon' in keys else None
        card.image = content['image'] if 'image' in keys else None
        card.url = content['url'] if 'url' in keys else None
        card.options = content['options'] if 'options' in keys else []
        card.tags = content['tags'] if 'tags' in keys else []
        card.priority = 0 if 'size' in card.tags else priority
        priority += 1
        card_objects.append(card)
    return card_objects

def get_due_date(user):
    for feature in user.features:
        if feature.name == 'DUE_DATE_MILLIS':
            return datetime.datetime.utcfromtimestamp(int(feature.value) // 1000)
    return None
