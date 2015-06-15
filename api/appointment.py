'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import datetime
import webapp2


from datastore import Appointment
from datastore import User

from google.appengine.ext import ndb
from api.renderer import get_appointment_json

class AppointmentAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
            self.put()
            return

        time_millis = self.request.get('time')
        minutes = self.request.get('minutes')

        if not time_millis:
            api.write_error(self.response, 400, 'Missing required parameter "time".')
            return

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if not minutes:
            minutes = 60

        time = datetime.datetime.utcfromtimestamp(int(time_millis) // 1000)
        appointment = Appointment(parent=user.key, time=time, minutes=int(minutes))
        appointment.put()

        api.write_message(self.response,
                          'Successfully added appointment %s' % (appointment.key.urlsafe()))

    def put(self):
        app_id = self.request.get('appointment_id')
        consumer_id = self.request.get('consumer_uuid')
        time_millis = self.request.get('time')
        minutes = self.request.get('minutes')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if not app_id:
            api.write_error(self.response, 400, 'Missing required parameter')
            return

        appointment = ndb.Key(urlsafe=app_id).get()

        if not appointment.consumer == user.key and not appointment.key.parent() == user.key:
            api.write_error(self.response, 403, 'Unauthorized')
            return

        remove_user = False
        if consumer_id and consumer_id[0] == '-':
            remove_user = True
            consumer_id = consumer_id[1:]

        if consumer_id:
            consumer = User.query(User.uuid == consumer_id).get()
            if consumer and remove_user and appointment.consumer == consumer:
                appointment.consumer = None
            elif consumer and not appointment.consumer:
                appointment.consumer = consumer.key

        if time_millis:
            appointment.time = datetime.datetime.utcfromtimestamp(int(time_millis) // 1000)
        if minutes:
            appointment.minutes = int(minutes)

        appointment.put()

        json = get_appointment_json(appointment)
        api.write_message(self.response, 'Updated appointment', extra={'appointments' : [json]})

    def get(self):
        start_millis = self.request.get('start_time')
        end_millis = self.request.get('end_time')
        uuid = self.request.get('uuid')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        provider = user
        if uuid:
            other = User.query(User.uuid == uuid).get()
            if other:
                provider = other

        appointments = []

        for appointment in get_provider_appointment_query(provider, start_millis, end_millis):
            # Show appts where
            #   1. User is provider
            #   2. There is no consumer so it is available slot
            #   3. Consumer is current user
            if provider == user or not appointment.consumer or appointment.consumer == user.key:
                appointments.append(get_appointment_json(appointment, provider))

        for appointment in get_consumer_appointment_query(user, start_millis, end_millis):
            # Show appts where
            #   1. User is the consumer and its not filtered for other user's appointment
            if provider == user:
                appointments.append(get_appointment_json(appointment, appointment.key.parent.get()))

        api.write_message(self.response, 'success', extra={'appointments' : appointments})

def get_provider_appointment_query(user, start_millis, end_millis):
    if start_millis:
        start = datetime.datetime.utcfromtimestamp(int(start_millis) // 1000)
    else:
        start = datetime.datetime.now()

    if end_millis:
        end = datetime.datetime.utcfromtimestamp(int(end_millis) // 1000)
        return Appointment.query(ndb.AND(Appointment.time > start, Appointment.time < end),
                                 ancestor=user.key)
    else:
        return Appointment.query(Appointment.time > start, ancestor=user.key).order(Appointment.time)

def get_consumer_appointment_query(user, start_millis, end_millis):
    if start_millis:
        start = datetime.datetime.utcfromtimestamp(int(start_millis) // 1000)
    else:
        start = datetime.datetime.now()

    if end_millis:
        end = datetime.datetime.utcfromtimestamp(int(end_millis) // 1000)
        return Appointment.query(ndb.AND(Appointment.consumer == user.key,
                                         ndb.AND(Appointment.time > start, Appointment.time < end)))
    else:
        return Appointment.query(Appointment.consumer == user.key).order(Appointment.time)
