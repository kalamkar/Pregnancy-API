'''
Created on Aug 28, 2015

@author: abhi
'''

import config
from datetime import datetime
import random
import urllib2
import sys

from utils import weekly_cards

URL = 'http://api.pregnansi.com/event'
AUTH_HEADER = 'UUID-TOKEN uuid="%s", token="%s"'


def get_poll_id(tags):
    poll_id = None
    for tag in tags:
        if tag.startswith('qid:'):
            return tag
    return poll_id

if __name__ == '__main__':
    auth_header = AUTH_HEADER % (config.SUPER_USER_UUID, config.SUPER_USER_AUTH)

    for key, week in weekly_cards.weekly['weeks'].iteritems():
        for card in week['cards']:
            poll_id = get_poll_id(card['tags'])
            if poll_id and 'options' in card.keys():
                option = card['options'][random.randint(0, len(card['options']) - 1)]
                tags = ['vote']
                tags.extend(card['tags'])
                millis = int((datetime.now() - datetime(1970, 1, 1)).total_seconds() * 1000)
                data = 'tags=%s&data=%s&time=%s' % (','.join(tags), urllib2.quote(option), str(millis))
                request = urllib2.Request(URL, data, {'Authorization': auth_header})
                print '%s %s %s' % (URL, data, urllib2.urlopen(request).read())



