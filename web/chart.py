'''
Created on Mar 27, 2015

@author: abhi
'''

import api.event
import datetime
import jinja2
import os
import string
import web
import webapp2


from datastore import Device

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

EVENT_TYPES = ['SENSOR_CONNECTED', 'SENSOR_DISCONNECTED', 'KICK_RECORDED', ]

class EventChart(webapp2.RequestHandler):

    def get(self):
        uuid = self.request.get('device_id')
        event_type = self.request.get('type')
        time_millis = self.request.get('time')
        start_millis = self.request.get('start_time')
        end_millis = self.request.get('end_time')
        chart_type = self.request.get('chart_type')

        if not uuid:
            web.write_error(self.response, 400, 'Missing required parameter')
            return

        query = Device.query(Device.uuid == uuid)
        if query.count() > 0:
            device = query.get()
        else:
            web.write_error(self.response, 404, 'Device %s not found' % (uuid))
            return

        start_millis = time_millis if time_millis else start_millis
        query = api.event.get_event_query(device, event_type, start_millis, end_millis)

        events = []
        calendar = {}
        timeline = []

        for event in query:
            millis = (event.time - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            events.append([int(millis), event.event_type])
            if event.event_type and event.event_type.find('KICK') == 0:
                date = event.time.date()
                try:
                    calendar[date] = calendar[date] + 1
                except:
                    calendar[date] = 1

        if chart_type and chart_type == 'detail':
            start_time = 0
            for event in sorted(events, key=lambda evt: evt[0]):
                if event[1] == 'SENSOR_CONNECTED':
                    start_time = event[0]
                elif event[1] == 'SENSOR_DISCONNECTED':
                    if start_time and start_time < event[0]:
                        timeline.append({'start': start_time, 'end': event[0],
                                         'type': 'Sensor Connected'})
                    start_time = 0
                elif event[1]:
                    timeline.append({'start': event[0], 'end': event[0] + 1,
                                     'type': string.capwords(event[1].replace('_', ' '))})

            template = JINJA_ENVIRONMENT.get_template('day.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('main.html')

        request = {'device_id': uuid, 'event_type': event_type,
                   'start_time': start_millis, 'end_time': end_millis}
        self.response.write(template.render({'events': events, 'timeline' : timeline,
                                             'calendar': calendar, 'request': request}))
