'''
Created on Apr 15, 2016

@author: abhi
'''

import json
import weekly_cards

cards = []

for week in range(1, 43):
    try:
        cards.extend(weekly_cards.weekly['weeks'][str(week)]['cards'])
    except:
        pass


print '# -*- coding: utf-8 -*-'
print 'cards = %s' % (json.dumps(cards, indent=2, ensure_ascii=False))

