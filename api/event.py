'''
Created on Sep 25, 2014

@author: abhijit
'''

import api
import datetime
import webapp2


from datastore import Device
from datastore import Event

from google.appengine.ext import ndb

class EventAPI(webapp2.RequestHandler):

    def post(self):
        uuid = self.request.get('device_id')
        event_type = self.request.get('type')
        time_millis = int(self.request.get('time'))

        if not uuid or not event_type or not time_millis:
            api.write_error(self.response, 400, 'Missing required parameter')
            return

        query = Device.query(Device.uuid == uuid)
        if query.count() > 0:
            device = query.get()
        else:
            api.write_error(self.response, 404, 'Device %s not found' % (uuid))
            return

        time = datetime.datetime.utcfromtimestamp(time_millis // 1000)
        time = time.replace(microsecond=time_millis % 1000 * 1000)
        event = Event(parent=device.key, event_type=event_type, time=time)
        event.put_async()

        api.write_message(self.response, 'Successfully added event %s' % (event.key.urlsafe()))

    def put(self):
        self.post()

    def get(self):
        uuid = self.request.get('device_id')
        event_type = self.request.get('type')
        time_millis = self.request.get('time')

        if not uuid:
            api.write_error(self.response, 400, 'Missing required parameter')
            return

        query = Device.query(Device.uuid == uuid)
        if query.count() > 0:
            device = query.get()
        else:
            api.write_error(self.response, 404, 'Device %s not found' % (uuid))
            return

        query = get_event_query(device, event_type, time_millis)
        events = []
        for event in query:
            millis = (event.time - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            events.append({'type': event.event_type, 'time': int(millis)})

        api.write_message(self.response, 'success', extra={'events' : events})

def get_event_query(device, event_type, time_millis):
    if event_type and time_millis:
        time = datetime.datetime.utcfromtimestamp(int(time_millis) // 1000)
        time = time.replace(microsecond=int(time_millis) % 1000 * 1000)
        return Event.query(ndb.AND(Event.event_type == event_type, Event.time > time),
                            ancestor=device.key)
    elif event_type:
        return Event.query(Event.event_type == event_type, ancestor=device.key)
    elif time_millis:
        time = datetime.datetime.utcfromtimestamp(int(time_millis) // 1000)
        time = time.replace(microsecond=int(time_millis) % 1000 * 1000)
        return Event.query(Event.time > time, ancestor=device.key)
    else:
        return Event.query(ancestor=device.key)
