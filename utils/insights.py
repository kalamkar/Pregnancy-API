'''
Created on Jul 28, 2015

@author: abhi
'''

import config
import datetime
import logging
import sys

from datastore import Insight
from datastore import Pair
from datastore import User
from utils import cards


def get_user_insights(user):
    insights = []
    for feature in user.features:
        if feature.name == 'DUE_DATE_MILLIS':
            due_date = datetime.datetime.utcfromtimestamp(int(feature.value) // 1000)
            start_date = due_date - datetime.timedelta(weeks=40)
            week = (datetime.datetime.now() - start_date).days / 7
            logging.info(cards.data['weeks'][str(week)])

            insights.extend(get_card_insights(cards.data['weeks'][str(week)]['cards']))
            if not insights:
                insights.extend(get_old_insights((due_date - datetime.datetime.now()).days, due_date))

    return insights

def get_card_insights(cards):
    insights = []
    if not cards:
        return []
    priority = 1
    for card in cards:
        insight = Insight(title=card['title'], tags=card['tags'], priority=priority)
        if 'size' in insight.tags.lower().split(','):
            insight.priority = 0
        priority += 1
        insights.append(insight)
    return insights

def get_old_insights(days, due_date):
    insights = []
    if days < -365:
        return insights
    if days < 0:
        insights.append(Insight(title='Congratulations!', tags='mother', priority=2))
    elif days < 7:
        insights.append(Insight(title='%d days to go!' % (days), tags='mother', priority=2))
    elif days < 275:
        insights.append(Insight(title='%d weeks %d days to go!' % (days / 7, days % 7),
                                tags='mother', priority=2))

    image_url = config.STORAGE_URL + config.IMAGES_BUCKET + 'eggplant.png'
    insights.append(Insight(title='Your baby is A inches and B lbs now. Roughly the size of a DDDD.',
                    tags='image:%s,mother' % (image_url), priority=3))
    insights.append(Insight(title='Expected birth date is %s.' % (due_date.strftime('%b %d %Y')), tags='baby',
                            priority=2))
    insights.append(Insight(title='Eat 1/2 apple everyday.', tags='mother', priority=1))
    return insights

if __name__ == "__main__":
    print get_user_insights(User(features=[Pair(name='DUE_DATE_MILLIS', value=sys.argv[1])]))
