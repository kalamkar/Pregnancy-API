'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import webapp2


from datastore import Message
from datastore import Group

from api.renderer import get_message_json

class MessageAPI(webapp2.RequestHandler):

    def post(self):
        uuid = self.request.get('group_uuid')
        text = self.request.get('text')

        if not uuid:
            api.write_error(self.response, 400, 'Missing required parameter, group_uuid')
            return

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        group = Group.query(Group.uuid == uuid).get()
        if not group:
            api.write_error(self.response, 404, 'Unknown or missing group for ')
            return

        message = Message(parent=group.key, sender=user.key, text=text)
        message.put()

        if group.public:
            api.search.update_public_index(message)
        else:
            api.search.update_private_index(message, user.uuid)

        gcm = []
        for member in group.members:
            if member == user.key:
                continue
            device = get_user_device(member.get())
            if device and device.device_type == 'APPLE':
                gcm.append(device.data)
            elif device and device.device_type == 'GOOGLE':
                gcm.append(device.data)
            elif device and device.device_type == 'EMAIL':
                api.email(device.data, get_message_json(message))
        if gcm:
            api.gcm(gcm, {'message': get_message_json(message), 'group_uuid': group.uuid})

        # Update the group update date
        group.put_async()

        api.write_message(self.response, 'Successfully added message')

    def get(self):
        uuid = self.request.get('group_uuid')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        group = None
        if uuid:
            group = Group.query(Group.uuid == uuid).get()

        if group:
            query = Message.query(ancestor=group.key).order(-Message.create_time)
        else:
            query = Message.query(Message.sender == user.key).order(-Message.create_time)

        messages = []
        for message in query:
            messages.append(get_message_json(message))

        api.write_message(self.response, 'success', extra={'messages' : messages})

def get_user_device(user):
    if not user or not user.devices:
        return None
    if len(user.devices) == 1:
        return user.devices[0]
    app_device = None
    email_device = None
    for device in user.devices:
        if device.device_type == 'EMAIL':
            email_device = device
        elif device.device_type in ['GOOGLE', 'APPLE', 'AMAZON']:
            app_device = device
    if app_device:
        return app_device
    if email_device:
        return email_device
    return None
