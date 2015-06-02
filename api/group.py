'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import logging
import webapp2
import uuid

from datastore import Group
from datastore import User

from user import get_user_json

from google.appengine.ext import ndb
from api import get_time_millis

class GroupAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
            self.put()
            return

        name = self.request.get('name')
        member_ids = self.request.get_all('member_uuid')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        group = Group(uuid=str(uuid.uuid4()))
        group.admins.append(user.key)
        group.members.append(user.key)
        group.name = name
        for member_id in member_ids:
            member = User.query(User.uuid == member_id).get()
            if member:
                group.members.append(member)
        group.put()

        api.write_message(self.response, 'success', extra={'groups' : [ get_group_json(group) ]})

    def put(self):
        uuid = self.request.get('group_uuid')
        name = self.request.get('name')
        admin_ids = self.request.get_all('admin_uuid')
        member_ids = self.request.get_all('member_uuid')

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

        if not user.key in group.admins:
            api.write_error(self.response, 403, 'User not allowed to update group')
            return

        group.name = name
        for admin_id in admin_ids:
            remove_user = False
            if admin_id and admin_id[0] == '-':
                remove_user = True
                admin_id = admin_id[1:]
            admin = User.query(User.uuid == admin_id).get()
            if admin:
                if remove_user:
                    if len(group.admins) > 1:
                        group.admins.remove(admin.key)
                    else:
                        api.write_error(self.response, 403, 'Cannot remove last admin')
                        return
                else:
                    group.admins.append(admin.key)
            else:
                logging.warn('Unknown user %s' % (admin_id))

        for member_id in member_ids:
            remove_user = False
            if member_id and member_id[0] == '-':
                remove_user = True
                member_id = member_id[1:]
            member = User.query(User.uuid == member_id).get()
            if member:
                if remove_user:
                    group.members.remove(member.key)
                else:
                    group.members.append(member.key)
            else:
                logging.warn('Unknown user %s' % (member_id))
        group.put()

        api.write_message(self.response, 'Updated group',
                          extra={'groups' : [ get_group_json(group) ]})


    def get(self):
        uuid = self.request.get('group_uuid')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        if uuid:
            query = Group.query(Group.uuid == uuid)
        else:
            query = Group.query(ndb.OR(Group.members == user.key,
                                       Group.admins == user.key)).order(-Group.update_time)

        groups = []
        for group in query:
            if user.key in group.members or user.key in group.admins:
                groups.append(get_group_json(group))

        api.write_message(self.response, 'success', extra={'groups' : groups})

def get_group_json(group):
    admins = []
    members = []

    for admin in group.admins:
        admins.append(get_user_json(admin.get()))

    for member in group.members:
        members.append(get_user_json(member.get()))

    json = {'uuid': group.uuid, 'name': group.name, 'admins': admins, 'members': members,
            'update_time': get_time_millis(group.update_time),
            'create_time': get_time_millis(group.create_time)}
    return json

