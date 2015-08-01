'''
Created on Jul 28, 2015

@author: abhi
'''

import sys
import csv
import json
import re

TAGS = {
         "baby's  milestone/fact":      ['milestone', 'baby'],
         "baby's size  visualization":  ['size'],
         "expectations for care":       ['care'],
         "polls":                       ['poll'],
         "symptoms":                    ['symptom'],
         "tips":                        ['tip'],
         "tips for dad":                ['tip', 'dad'],
         }

def parse_card(content, card_type, week):
    json = {'type': card_type}
    result = re.search('(?P<url>https?://[^\s]+)', content)
    if result:
        json['url'] = result.group('url')
        content = content.replace(json['url'], '')
    json['tags'] = list(TAGS[card_type.lower()])
    json['tags'].append('week:%d' % (week))

    single_options = re.findall('#\d\. [^#]+', content)
    if single_options and ('poll' in json['tags'] or 'symptom' in json['tags']):
        options = []
        for option in single_options:
            if option:
                content = content.replace(option, '')
                options.append(re.sub('^#\d\.', '', option).strip())
        json['options'] = options

    multi_options = re.findall('@\d\. [^@]+', content)
    if multi_options and ('poll' in json['tags'] or 'symptom' in json['tags']):
        options = []
        for option in multi_options:
            if option:
                content = content.replace(option, '')
                options.append(re.sub('^@\d\.', '', option).strip())
        json['options'] = options
        json['tags'].append('multi_select')

    json['text'] = content.replace('%', '').replace('//', '').strip()

    return json

def parse_week(week, types):
    json = {}
    json['title'] = week[0]
    week_number = int(re.search('(?P<week>[0-9]+)', week[0]).group('week'))
    json['cards'] = []
    for i in range(1, len(week)):
        if week[i] and week[i].strip():
            json['cards'].append(parse_card(week[i], types[i], week_number))
    return (week_number, json)

weeks = {}
with open(sys.argv[1]) as tsv:
    lines = csv.reader(tsv, dialect="excel-tab")
    columns = zip(*[line for line in lines])
    type_column = columns[0]
    for column in columns[1:]:
        (week_number, week) = parse_week(column, type_column)
        weeks[week_number] = week
    print 'data = %s' % (json.dumps({'weeks': weeks}, indent=4))

