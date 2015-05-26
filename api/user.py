'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import uuid
import webapp2

from datastore import User
from datastore import Device

class UserAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
            self.put()
            return

        user = User(uuid=str(uuid.uuid4()))
        user.put()

        json = {'id': user.key.urlsafe(), 'uuid': user.uuid,
                'update_time': user.update_time.isoformat(' '),
                'create_time': user.create_time.isoformat(' ')}

        api.write_message(self.response, 'success', extra={'user' : json})

    def put(self):
        name = self.request.get('name')
        email = self.request.get('email')
        push_token = self.request.get('token')
        device_type = self.request.get('type')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        if name:
            user.name = name

        token_updated = False
        for device in user.devices:
            if email and device.device_type == 'EMAIL':
                device.data = email
            elif push_token and device_type and device.device_type == device_type:
                device.data = push_token
                token_updated = True

        if not token_updated and push_token:
            user.devices.append(Device(device_type=device_type, data=push_token))

        user.last_location = api.get_geo_point(self.request)
        user.put_async()

        api.write_message(self.response, 'Updated user')


    def get(self):
        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        json = get_user_json(user, public=False)
        api.write_message(self.response, 'success', extra={'user' : json})

def get_user_json(user, public=True):
    email = None
    for device in user.devices:
        if email and device.device_type == 'EMAIL':
            email = device.data
    json = {'uuid': user.uuid, 'name': user.name,
            'update_time': user.update_time.isoformat(' '),
            'create_time': user.create_time.isoformat(' ')}
    if not public:
        json['email'] = email
    return json

