'''
Created on Jul 28, 2015

@author: abhi
'''

import sys
import csv
import hashlib
import json
import re

URL_PATTERN = re.compile('(?P<url>https?://[^\s]+)')
PHOTO_PATTERN = re.compile('#photo#(?P<photo>https?://[^\s]+)')

TAGS = {
         "baby's  milestone/fact":      ['milestone', 'baby'],
         "baby's size  visualization":  ['size'],
         "expectations for care":       ['care', 'action:to_do'],
         "polls":                       ['poll'],
         "symptoms":                    ['symptom', 'gender:female'],
         "tip/factoid":                 ['tip'],
         "tips for dad":                ['tip', 'gender:male'],
         }

def parse_card(content, card_type, week, card_number):
    json = {'type': card_type}
    result = URL_PATTERN.search(content)
    if result:
        json['url'] = result.group('url')
        content = content.replace(json['url'], '')
    result = PHOTO_PATTERN.search(content)
    if result:
        json['image'] = result.group('photo')
        content = content.replace(json['image'], '')
        content = content.replace('#photo#', '')
    json['tags'] = list(TAGS[card_type.lower()])
    json['tags'].append('week:%d' % (week))
    json['tags'].append('card:%d' % (card_number))

    single_options = re.findall('#\d ?\. ?[^#]+', content)
    if single_options:  # and ('poll' in json['tags'] or 'symptom' in json['tags']):
        options = []
        for option in single_options:
            if option:
                content = content.replace(option, '')
                options.append(re.sub('^#\d\.', '', option).strip())
        json['options'] = options
        json['tags'].append('qid:%s' % (hashlib.sha224(','.join(json['tags'])).hexdigest()))

    multi_options = re.findall('@\d ?\. ?[^@]+', content)
    if multi_options and ('poll' in json['tags'] or 'symptom' in json['tags']):
        options = []
        for option in multi_options:
            if option:
                content = content.replace(option, '')
                options.append(re.sub('^@\d\.', '', option).strip())
        json['options'] = options
        json['tags'].append('multi_select')
        json['tags'].append('qid:%s' % (hashlib.sha224(','.join(json['tags'])).hexdigest()))

    json['text'] = content.replace('%', '').replace('//', '').strip()

    return json

def parse_week(week, types):
    json = {}
    json['title'] = week[0]
    week_number = int(re.search('(?P<week>[0-9]+)', week[0]).group('week'))
    json['cards'] = []
    for i in range(1, len(week)):
        if week[i] and week[i].strip():
            json['cards'].append(parse_card(week[i], types[i], week_number, i))
    return (week_number, json)

weeks = {}
with open(sys.argv[1]) as tsv:
    lines = csv.reader(tsv, dialect="excel-tab")
    columns = zip(*[line for line in lines])
    type_column = columns[0]
    for column in columns[1:]:
        (week_number, week) = parse_week(column, type_column)
        weeks[week_number] = week
    print 'weekly = %s' % (json.dumps({'weeks': weeks}, indent=2, ensure_ascii=False))

