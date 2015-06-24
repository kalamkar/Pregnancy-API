'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import config
import cloudstorage as gcs
import random
import uuid
import webapp2

from datastore import User, Recovery
from datastore import Device
from datastore import Pair
from api.renderer import get_user_json
from api.search import update_index

class UserAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
            self.put()
            return

        name = self.request.get('name')
        email = self.request.get('email')
        push_token = self.request.get('token')
        device_type = self.request.get('type')

        if not push_token or not device_type:
            api.write_error(self.response, 400, 'Missing required parameter, token or type')
            return

        user = User(uuid=str(uuid.uuid4()), auth=str(uuid.uuid4()))
        if name:
            user.name = name
        if email:
            user.devices.append(Device(device_type='EMAIL', data=email))
        user.devices.append(Device(device_type=device_type.upper(), data=push_token))
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
            api.write_error(self.response, 403, 'Unknown or missing user')
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
            user.devices.append(Device(device_type=device_type.upper(), data=push_token))
        if not email_updated and email:
            user.devices.append(Device(device_type='EMAIL', data=email))

        for feature in features:
            update_feature(user, feature)

        user.last_location = api.get_geo_point(self.request)
        user.insights = api.make_insights(user)
        user.put()
        update_index(user)

        json = get_user_json(user, public=False)
        api.write_message(self.response, 'Updated user', extra={'users' : [json]})


    def get(self):
        uuid = self.request.get('uuid')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        json = None
        if uuid:
            other = User.query(User.uuid == uuid).get()
            if other:
                json = get_user_json(other)

        if not json:
            json = get_user_json(user, public=False)

        api.write_message(self.response, 'success', extra={'users' : [json]})

class UserPhotoAPI(webapp2.RequestHandler):

    def post(self):
        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return
        try:
            uploaded_file = self.request.POST['file']
            if not uploaded_file.type:
                api.write_error(self.response, 400, 'Missing content type')
                return
        except:
            uploaded_file = None

        if uploaded_file == None:
            api.write_error(self.response, 400, 'Missing content')
            return

        filename = config.PROFILE_BUCKET + user.uuid
        gcs_file = gcs.open(filename, mode='w', content_type=uploaded_file.type,
                            options={'x-goog-acl': 'public-read',
                                     'Cache-Control' : 'public,max-age=%d' % (config.MEDIA_MAX_AGE)})
        gcs_file.write(uploaded_file.file.read())
        gcs_file.close();

        api.write_message(self.response, 'success')

class UserRecoveryAPI(webapp2.RequestHandler):

    def post(self):
        email = self.request.get('email')
        push_token = self.request.get('token')
        device_type = self.request.get('type')

        users = User.query(User.devices.data == email)
        if not users:
            api.write_error(self.response, 404, 'User not found')
            return

        push_token_found = False;
        first_user = None
        for user in users:
            if not user or not user.devices:
                continue
            if not first_user:
                first_user = user
            for device in user.devices:
                if not device.device_type in ['GOOGLE', 'APPLE', 'AMAZON']:
                    continue
                if device.device_type == device_type and device.data == push_token:
                    push_token_found = True
                    if device.device_type == 'GOOGLE':
                        api.gcm([push_token], {'user': get_user_json(user, public=False)})
                    elif device.device_type == 'APPLE':
                        # Until we can deliver data to iOS app directly, use email for them
                        push_token_found = False

        if not push_token_found and first_user:
            # Is this correct to pick first user?
            if not first_user.recovery:
                first_user.recovery = Recovery()
            first_user.recovery.code = random.randint(1000, 9999)
            api.email(email, 'Account recovery code is %s' % (first_user.recovery.code))
            first_user.put()

        api.write_message(self.response, 'success')


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

