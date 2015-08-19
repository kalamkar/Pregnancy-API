'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import datetime

from google.appengine.ext import ndb
import webapp2

import api
from datastore import Event
from renderer import get_event_json


class EventAPI(webapp2.RequestHandler):

    def post(self):
        event_type = self.request.get('type')
        time_millis = int(self.request.get('time'))
        data = self.request.get('data')
        tags = self.request.get('tags')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        # TODO(abhi): Remove this hack once client changes type to tags
        if event_type:
            tags = event_type

        time = datetime.datetime.utcfromtimestamp(time_millis // 1000)
        time = time.replace(microsecond=time_millis % 1000 * 1000)
        event = Event(parent=user.key, tags=tags.lower().split(','), time=time, data=data)
        event.put_async()

        api.write_message(self.response, 'Successfully added event %s' % (event.key.urlsafe()))

    def get(self):
        event_type = self.request.get('type')
        start_millis = self.request.get('start_time')
        end_millis = self.request.get('end_time')
        tags = self.request.get('tags')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        # TODO(abhi): Remove this hack once client changes type to tags
        if event_type:
            tags = event_type

        query = get_event_query(user, tags, start_millis, end_millis)
        events = []
        for event in query:
            events.append(get_event_json(event))

        api.write_message(self.response, 'success', extra={'events' : events})


def get_event_query(user, tags, start_millis, end_millis):
    if end_millis:
        end = get_time_from_millis(end_millis)
    else:
        end = datetime.datetime.now()

    if tags and start_millis:
        start = get_time_from_millis(start_millis)
        return Event.query(ndb.AND(Event.tags.IN(tags.lower().split(',')),
                                   ndb.AND(Event.time > start, Event.time < end)),
                            ancestor=user.key).order(-Event.time)
    elif start_millis:
        start = get_time_from_millis(start_millis)
        return Event.query(ndb.AND(Event.time > start, Event.time < end),
                           ancestor=user.key).order(-Event.time)
    elif tags:
        return Event.query(Event.tags.IN(tags.lower().split(',')),
                            ancestor=user.key).order(-Event.time)
    else:
        return Event.query(ancestor=user.key).order(-Event.time)


def get_time_from_millis(millis):
    time = datetime.datetime.utcfromtimestamp(int(millis) // 1000)
    return time.replace(microsecond=int(millis) % 1000 * 1000)
