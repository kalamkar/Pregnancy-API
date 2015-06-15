'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import uuid
import webapp2

from datastore import User
from datastore import Device
from datastore import Pair
from api.renderer import get_user_json
from api.search import update_index

class UserAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
            self.put()
            return

        push_token = self.request.get('token')
        device_type = self.request.get('type')

        if not push_token or not device_type:
            api.write_error(self.response, 400, 'Missing required parameter, token or type')
            return

        user = User(uuid=str(uuid.uuid4()))
        user.devices.append(Device(device_type=device_type, data=push_token))
        user.put()
        update_index(user)

        json = get_user_json(user, public=False)
        json['id'] = user.key.urlsafe();

        api.write_message(self.response, 'success', extra={'users' : [json]})

    def put(self):
        name = self.request.get('name')
        email = self.request.get('email')
        push_token = self.request.get('token')
        device_type = self.request.get('type')
        features = self.request.get_all('feature')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if name:
            user.name = name

        token_updated = False
        email_updated = False
        for device in user.devices:
            if email and device.device_type == 'EMAIL':
                device.data = email
                email_updated = True
            elif push_token and device_type and device.device_type == device_type:
                device.data = push_token
                token_updated = True

        if not token_updated and push_token:
            user.devices.append(Device(device_type=device_type, data=push_token))
        if not email_updated and email:
            user.devices.append(Device(device_type='EMAIL', data=email))

        for feature in features:
            update_feature(user, feature)

        user.last_location = api.get_geo_point(self.request)
        user.put()
        update_index(user)

        json = get_user_json(user, public=False)
        api.write_message(self.response, 'Updated user', extra={'users' : [json]})


    def get(self):
        uuid = self.request.get('uuid')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        json = None
        if uuid:
            other = User.query(User.uuid == uuid).get()
            if other:
                json = get_user_json(other)

        if not json:
            json = get_user_json(user, public=False)

        api.write_message(self.response, 'success', extra={'users' : [json]})

def update_feature(user, new_feature):
    if not new_feature:
        return
    name, value = new_feature.split('=', 1)
    if not name:
        return
    for feature in user.features:
        if feature.name == name:
            feature.value = value
            return
    user.features.append(Pair(name=name, value=value))

