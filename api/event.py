'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import config
import datetime
import json
import numpy
import random
import StringIO

from google.appengine.ext import ndb
import webapp2
import matplotlib.pyplot as charts

import api
from datastore import Event
from renderer import get_event_json

class EventAPI(webapp2.RequestHandler):

    def post(self):
        time_millis = self.request.get('time')
        data = self.request.get('data')
        tags = self.request.get('tags')

        try:
            referer = self.request.headers['Referer']
        except:
            referer = ''

        user = api.get_user(self.request)
        if not user and referer.find('/poll') < 0:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if not tags or not time_millis:
            api.write_error(self.response, 400, 'Missing required parameter.')
            return

        tags = tags.lower().split(',')
        time = api.get_time_from_millis(time_millis)
        if user:
            event = Event(parent=user.key, tags=tags, time=time, data=data)
        else:
            event = Event(tags=tags, time=time, data=data)
        event.put_async()

        api.write_message(self.response, 'Successfully added event %s' % (event.key.urlsafe()))

    def get(self):
        start_millis = self.request.get('start_time')
        end_millis = self.request.get('end_time')
        tags = self.request.get('tags')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if not tags:
            api.write_error(self.response, 400, 'Missing required parameter, tags.')
            return

        tags = tags.lower().split(',')
        query = get_user_event_query(user, tags, start_millis, end_millis)
        events = []
        for event in query:
            events.append(get_event_json(event))

        api.write_message(self.response, 'success', extra={'events' : events})


class EventChartAPI(webapp2.RequestHandler):
    def get(self):
        tags = self.request.get('tags')
        start_millis = self.request.get('start_time')
        end_millis = self.request.get('end_time')
        chart_type = self.request.get('type')
        tz_offset = self.request.get('tz_offset')
        debug = self.request.get('debug')

        if not tags:
            api.write_error(self.response, 400, 'Missing required parameter, tags')
            return

        tags = tags.lower().split(',')
        query = get_user_event_query(None, tags, start_millis, end_millis)
        results = {}
        events = []
        xdata = []
        ydata = []
        for event in query:
            if debug:
                events.append(get_event_json(event))
            try:
                if chart_type and chart_type == 'time':
                    measurement = json.loads(event.data)
                    xdata.append(api.get_local_time(event.time, tz_offset))
                    ydata.append(int(measurement['value']))
                else:
                    results[event.data] += 1
            except:
                results[event.data] = 1

        if debug:
            api.write_message(self.response, 'success', extra={'events' : events})
            return

        if query.count() == 0:
            api.write_error(self.response, 404, 'Not enough data points for chart.')
            return

        if chart_type and chart_type == 'time':
            # Reverse the data as we query events in descending order of time
            xdata.reverse()
            ydata.reverse()
            show_vertical_bars(self.response, xdata, ydata)
        else:
            show_horizontal_bars(self.response, results)


def show_vertical_bars(response, xdata, ydata):
    output = StringIO.StringIO()
    try:
        xlabels = []
        for time in xdata:
            xlabels.append(time.strftime('%a'))

        figure, axis1 = charts.subplots()
        axis1.bar(range(len(ydata)), ydata, align='center', color='#F391A4', linewidth=0)

        rects = axis1.patches
        ylabels = ["%dk" % int(steps / 1000)  for steps in ydata]
        for rect, label in zip(rects, ylabels):
            height = rect.get_height()
            axis1.text(rect.get_x() + rect.get_width() / 2, height, label, ha='center', va='top',
                       color='w')

        charts.xticks(range(len(xlabels)), xlabels, family='sans-serif')
        charts.yticks([])
        charts.tick_params(left='off', right='off', top='off', bottom='off')
        charts.box(False)

        figure.set_size_inches(5, 3)
        figure.savefig(output, dpi=100, orientation='landscape', format='png', transparent=True,
                        frameon=False, bbox_inches='tight', pad_inches=0)
    except:
        pass

    response.headers['Content-Type'] = 'image/png'
    # self.response.headers['Cache-Control'] = 'public,max-age=%d' % (config.CHART_MAX_AGE)
    response.out.write(output.getvalue())
    output.close()

def show_horizontal_bars(response, results):
    output = StringIO.StringIO()
    try:
        charts.clf()
        total = sum(results.values())
        labels = []
        for label in results.keys():
            labels.append(str(results[label] * 100 / total) + '% say ' + label)

        colors = list(config.CHART_COLORS)
        random.shuffle(colors)
        charts.barh(range(len(labels)), results.values(), align='center', linewidth=0,
                            color=colors)
        charts.yticks(range(len(labels)), labels, family='sans-serif', ha='left', x=0.03,
                        color='#808080')
        charts.xticks([])
        charts.tick_params(left='off', right='off')
        charts.box(False)

        figure = charts.gcf()
        figure.set_size_inches(5, 3)
        figure.savefig(output, dpi=100, orientation='landscape', format='png', transparent=True,
                        frameon=False, bbox_inches='tight', pad_inches=0)
    except:
        pass

    response.headers['Content-Type'] = 'image/png'
    # self.response.headers['Cache-Control'] = 'public,max-age=%d' % (config.CHART_MAX_AGE)
    response.out.write(output.getvalue())
    output.close()


def get_user_event_query(user, tags, start_millis, end_millis):
    end = api.get_time_from_millis(end_millis)
    if not end:
        end = datetime.datetime.now()

    start = api.get_time_from_millis(start_millis)
    if not start:
        start = api.get_time_from_millis('0')

    if user:
        return Event.query(ndb.AND(Event.tags.IN(tags), Event.time > start, Event.time < end),
                           ancestor=user.key).order(-Event.time)
    else:
        return Event.query(ndb.AND(Event.tags.IN(tags), Event.time > start, Event.time < end)).\
                            order(-Event.time)


def get_average_measurement(user, tags, start_millis, end_millis):
    values = []
    query = get_user_event_query(user, tags, start_millis, end_millis)
    for event in query:
        try:
            measurement = json.loads(event.data)
            values.append(int(measurement['value']))
        except:
            continue

    return numpy.mean(values)

