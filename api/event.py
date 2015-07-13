'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import datetime
import webapp2


from datastore import Event

from google.appengine.ext import ndb
from api import get_time_millis

class EventAPI(webapp2.RequestHandler):

    def post(self):
        event_type = self.request.get('type')
        time_millis = int(self.request.get('time'))
        data = self.request.get('data')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        time = datetime.datetime.utcfromtimestamp(time_millis // 1000)
        time = time.replace(microsecond=time_millis % 1000 * 1000)
        event = Event(parent=user.key, event_type=event_type, time=time, data=data)
        event.put_async()

        api.write_message(self.response, 'Successfully added event %s' % (event.key.urlsafe()))

    def get(self):
        event_type = self.request.get('type')
        start_millis = self.request.get('start_time')
        end_millis = self.request.get('end_time')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        query = get_event_query(user, event_type, start_millis, end_millis)
        events = []
        for event in query:
            events.append({'type': event.event_type, 'time': get_time_millis(event.time)})

        api.write_message(self.response, 'success', extra={'events' : events})

def get_event_query(user, event_type, start_millis, end_millis):
    if end_millis:
        end = get_time_from_millis(end_millis)
    else:
        end = datetime.datetime.now()

    if event_type and start_millis:
        start = get_time_from_millis(start_millis)
        return Event.query(ndb.AND(Event.event_type == event_type,
                                   ndb.AND(Event.time > start, Event.time < end)),
                            ancestor=user.key)
    elif start_millis:
        start = get_time_from_millis(start_millis)
        return Event.query(ndb.AND(Event.time > start, Event.time < end), ancestor=user.key)
    elif event_type:
        return Event.query(Event.event_type == event_type, ancestor=user.key).order(-Event.time)
    else:
        return Event.query(ancestor=user.key).order(-Event.time)

def get_time_from_millis(millis):
    time = datetime.datetime.utcfromtimestamp(int(millis) // 1000)
    return time.replace(microsecond=int(millis) % 1000 * 1000)
