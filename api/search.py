'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import json
import logging
import webapp2

from google.appengine.api import search
from google.appengine.ext import ndb

from datastore import Message
from datastore import Group
from datastore import User
from api.renderer import get_message_json
from api.renderer import get_group_json
from api.renderer import get_user_json


SEARCH_INDEX = 'SEARCH_INDEX'

class SearchAPI(webapp2.RequestHandler):

    def get(self):
        query = self.request.get('q')
        location = None
        if self.request.get('nearby'):
            location = api.get_geo_point(self.request)

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        object_keys = search_objects(query, location)
        results = []
        result = ndb.get_multi_async(object_keys)
        ndb.Future.wait_all(result)
        for handle in result:
            data = {}
            obj = handle.get_result()
            if isinstance(obj, Message) and api.is_user_allowed_message_view(user, obj):
                data['message'] = get_message_json(obj)
            elif isinstance(obj, Group) and api.is_user_allowed_group_view(user, obj):
                data['group'] = get_group_json(obj)
            elif isinstance(obj, User):
                data['user'] = get_user_json(obj)

            if data:
                results.append(data)

        api.write_message(self.response, 'success', extra={'results' : results})

def search_objects(query, location):
    object_keys = []

    index_query = 'text: %s ' % (query)
    if location and location.latlon:
        geopt = location.latlon
        radius = 25000
        index_query += 'distance(location, geopoint(%s, %s)) < %s' % (geopt.lat, geopt.lon, radius)
    logging.info('Querying search index %s' % index_query)
    index = search.Index(name=SEARCH_INDEX)
    try:
        results = index.search(index_query)
        for doc in results:
            object_keys.append(ndb.Key(urlsafe=doc.doc_id))
    except search.Error:
        logging.exception('Search failed')

    return object_keys

def update_index(obj):
    try:
        location = None
        data = {}
        if isinstance(obj, Message):
            data = get_message_json(obj)
        elif isinstance(obj, Group):
            data = get_group_json(obj)
        elif isinstance(obj, User):
            data = get_user_json(obj, public=False)
            location = obj.last_location

        data['update_time'] = None
        data['create_time'] = None

        index = search.Index(name=SEARCH_INDEX)
        fields = [search.TextField(name='text', value=json.dumps(data))]
        if location and location.latlon:
            latlon = location.latlon
            fields.append(search.GeoField(name='location',
                                          value=search.GeoPoint(latlon.lat, latlon.lon)))
        index.put(search.Document(doc_id=obj.key.urlsafe(), fields=fields))
    except:
        logging.warn('Adding question %s to search index failed.' % (str(obj)))
