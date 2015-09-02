'''
Created on Jul 28, 2015

@author: abhi
'''

import datetime
import logging
import math
import re
import sys

import api
from api.event import get_average_measurement
from api.renderer import get_card_json
from datastore import Card
from datastore import Pair
from datastore import User
from utils import data_cards
from utils import system_cards
from utils import weekly_cards


def update_user_cards(user):
    now = datetime.datetime.now()
    current_cards = {}
    pregnancy_week = get_pregnancy_week(user)
    for card in Card.query(ancestor=user.key):
        # Expire cards for previous week
        card_week = get_card_week(card)
        if card_week and pregnancy_week and card.expire_time and card.expire_time > now \
            and not (card_week == pregnancy_week):
            logging.info('Expiring card with tags %s for %s' % (card.tags, user.name))
            card.expire_time = now
            card.put_async()

        # Expired cards are not current (visible) cards
        if card.expire_time and card.expire_time < now:
            continue

        current_cards[get_card_type(card)] = card

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

        # Skip the card if it is already there
        if get_card_type(card) in current_cards.keys():
            continue

        futures.append(card.put_async())

    if get_due_date(user):
        for card_id, card in current_cards.iteritems():
            if 'action:due_date' in card.tags:
                card.key.delete_async()

    for future in futures:
        api.search.update_private_index(future.get_result().get(), user.uuid)


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
    week = get_pregnancy_week(user)
    if not week:
        # Use calendar week if pregnancy week is not available
        week = datetime.datetime.now().isocalendar()[1]
    cards = []
    for content in data_cards.data['cards']:
        card = make_card(content, user)
        card.tags.append('week:%d' % week)
        card.priority = 2
        cards.append(card)

    return cards

def get_week_based_cards(user):
    due_date = get_due_date(user)
    if not due_date:
        return []

    start_date = due_date - datetime.timedelta(weeks=40)
    week = get_pregnancy_week(user)
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
    if 'size' in cards_by_tag.keys():
        card = cards_by_tag['size'].pop(0)
        card.priority = 0

    card_type_order = ['symptom', 'poll', 'care', 'tip']
    card_type_index = 0
    priority = 3
    while len(cards_by_tag):
        card_type = card_type_order[card_type_index]
        try:
            card = cards_by_tag[card_type].pop(0)
            card.priority = priority
            priority += 1
        except:
            card_type_order.remove(card_type)
            if not card_type_order:
                break

        card_type_index = card_type_index + 1 if card_type_index + 1 < len(card_type_order) else 0

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

def get_pregnancy_week(user):
    try:
        due_date = get_due_date(user)
        start_date = due_date - datetime.timedelta(weeks=40)
        return int((datetime.datetime.now() - start_date).days / 7)
    except:
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
    variables['name'] = user.name.split()[0] if user.name else ''
    last_week_start = api.get_last_week_start()
    last_week_end = last_week_start + datetime.timedelta(days=7)
    weekly_avg_steps = get_average_measurement(user, ['STEPS'], api.get_time_millis(last_week_start),
                                               api.get_time_millis(last_week_end))
    weekly_avg_sleep = get_average_measurement(user, ['SLEEP'], api.get_time_millis(last_week_start),
                                               api.get_time_millis(last_week_end))
    if weekly_avg_steps and not math.isnan(weekly_avg_steps):
        variables['weekly_average_steps'] = str(int(weekly_avg_steps))
    if weekly_avg_sleep and not math.isnan(weekly_avg_sleep):
        variables['weekly_average_sleep'] = str(weekly_avg_sleep)
    return variables

def get_card_type(card):
    tags = list(card.tags)
    if 'archived' in tags:
        tags.remove('archived')
    tags.sort()
    return ','.join(tags)

def get_card_week(card):
    week = None
    for tag in card.tags:
        if tag.startswith('week:'):
            try:
                return int(tag.split(':')[1])
            except:
                pass

    return week


if __name__ == '__main__':
    user = User()
    user.features.append(Pair(name='DUE_DATE_MILLIS', value=sys.argv[1]))
    for card in get_week_based_cards(user):
        print get_card_json(card)
