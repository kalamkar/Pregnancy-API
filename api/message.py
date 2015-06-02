'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import webapp2


from datastore import Message
from datastore import Group

from user import get_user_json
from api import get_time_millis

class MessageAPI(webapp2.RequestHandler):

    def post(self):
        uuid = self.request.get('group_uuid')
        text = self.request.get('text')

        if not uuid:
            api.write_error(self.response, 400, 'Missing required parameter')
            return

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        group = Group.query(Group.uuid == uuid).get()
        if not group:
            api.write_error(self.response, 404, 'Unknown or missing group')
            return

        message = Message(parent=group.key, sender=user.key, text=text)
        message.put_async()

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

def get_message_json(message):
    return {'sender': get_user_json(message.sender.get()), 'text': message.text,
            'create_time': get_time_millis(message.create_time)}


