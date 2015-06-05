'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

from api import get_time_millis


def get_user_json(user, public=True):
    json = {'uuid': user.uuid, 'name': user.name,
            'update_time': get_time_millis(user.update_time),
            'create_time': get_time_millis(user.create_time)}
    if user.last_location and user.last_location.name:
        json['location'] = user.last_location.name

    if not public:
        email = None
        if user.devices:
            for device in user.devices:
                if device.data and device.device_type == 'EMAIL':
                    email = device.data
        json['email'] = email
        features = {}
        for feature in user.features:
            if feature.name and not feature.name[0] == '_':
                features[feature.name] = feature.value
        json['features'] = features
    return json


def get_message_json(message):
    return {'sender': get_user_json(message.sender.get()), 'text': message.text,
            'create_time': get_time_millis(message.create_time)}



def get_group_json(group):
    admins = []
    members = []

    for admin in group.admins:
        admins.append(get_user_json(admin.get()))

    for member in group.members:
        members.append(get_user_json(member.get()))

    json = {'uuid': group.uuid, 'name': group.name, 'admins': admins, 'members': members,
            'public': group.public,
            'update_time': get_time_millis(group.update_time),
            'create_time': get_time_millis(group.create_time)}
    return json

